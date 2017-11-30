import logging

import keras

from cluster.neuralnet.neuralnet_node import NeuralNetNode
from cluster.neuralnet_model import resnet
from cluster.neuralnet_model.inception_resnet_v1 import create_inception_resnet_v1
from cluster.neuralnet_model.inception_resnet_v2 import create_inception_resnet_v2
from cluster.neuralnet_model.inception_v4 import create_inception_v4
from master.workflow.netconf.workflow_netconf import WorkFlowNetConf
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ReduceLROnPlateau, CSVLogger, EarlyStopping
from common.graph.nn_graph_manager import NeuralNetModel
import tensorflow as tf
import numpy as np
from cluster.common.train_summary_info import TrainSummaryInfo

class NeuralNetNodeImage(NeuralNetNode):
    def keras_get_model(self):
        self.optimizer = self.netconf["config"]["optimizer"]

        keras.backend.tensorflow_backend.clear_session()
        try:
            self.model = keras.models.load_model(self.last_chk_path)
            logging.info("Train Restored checkpoint from:" + self.last_chk_path)
        except Exception as e:
            logging.info("None to restore checkpoint. Initializing variables instead." + self.last_chk_path)
            logging.info(e)
            if self.net_type == 'inceptionv4':
                self.model = create_inception_v4()
            elif self.net_type == 'inception_resnet_v1':
                self.model = create_inception_resnet_v1()
            elif self.net_type == 'inception_resnet_v2':
                self.model = create_inception_resnet_v2()
            elif self.net_type == 'resnet':
                numoutputs = self.netconf["config"]["layeroutputs"]

                if numoutputs == 18:
                    self.model = resnet.ResnetBuilder.build_resnet_18((self.channel, self.x_size, self.y_size), self.labels_cnt)
                elif numoutputs == 34:
                    self.model = resnet.ResnetBuilder.build_resnet_34((self.channel, self.x_size, self.y_size), self.labels_cnt)
                elif numoutputs == 50:
                    self.model = resnet.ResnetBuilder.build_resnet_50((self.channel, self.x_size, self.y_size), self.labels_cnt)
                elif numoutputs == 101:
                    self.model = resnet.ResnetBuilder.build_resnet_101((self.channel, self.x_size, self.y_size), self.labels_cnt)
                elif numoutputs == 152:
                    self.model = resnet.ResnetBuilder.build_resnet_152((self.channel, self.x_size, self.y_size), self.labels_cnt)
                elif numoutputs == 200:
                    self.model = resnet.ResnetBuilder.build_resnet_200((self.channel, self.x_size, self.y_size), self.labels_cnt)

        self.model.compile(loss='categorical_crossentropy', optimizer=self.optimizer, metrics=['accuracy'])

    def train_run(self, input_data, test_data):
        '''
        Train Run
        :param input_data: 
        :param test_data: 
        :return: 
        '''
        self.epoch = self.netconf["param"]["epoch"]
        self.data_augmentation = self.netconf["param"]["augmentation"]

        self.lr_reducer = ReduceLROnPlateau(monitor='val_loss', factor=np.sqrt(0.1), cooldown=0, patience=5, min_lr=0.5e-6)
        self.early_stopper = EarlyStopping(monitor='val_acc', min_delta=0.001, patience=10)
        self.csv_logger = CSVLogger('resnet.csv')

        try:
            while_cnt = 0
            self.loss = 0
            self.acc = 0
            self.val_loss = 0
            self.val_acc = 0

            input_data.reset_pointer()
            test_data.reset_pointer()

            test_set = test_data[0:test_data.data_size()]
            x_tbatch = self.get_convert_img_x(test_set[0], self.x_size, self.y_size, self.channel) # img_data_batch
            y_tbatch = self.get_convert_img_y(test_set[1], self.labels, self.labels_cnt) # label_data_batch

            while (input_data.has_next()):
                input_set = input_data[0:input_data.data_size()]
                x_batch = self.get_convert_img_x(input_set[0], self.x_size, self.y_size, self.channel)  # img_data_batch
                y_batch = self.get_convert_img_y(input_set[1], self.labels, self.labels_cnt)  # label_data_batch

                if self.data_augmentation == "N" or self.data_augmentation == "n":
                    history = self.model.fit(x_batch, y_batch,
                                             batch_size=self.batch_size,
                                             epochs=self.epoch,
                                             validation_data=(x_tbatch, y_tbatch),
                                             shuffle=True,
                                             callbacks=[self.lr_reducer, self.early_stopper, self.csv_logger])
                else:
                    # This will do preprocessing and realtime data augmentation:
                    datagen = ImageDataGenerator(
                        featurewise_center=False,  # set input mean to 0 over the dataset
                        samplewise_center=False,  # set each sample mean to 0
                        featurewise_std_normalization=False,  # divide inputs by std of the dataset
                        samplewise_std_normalization=False,  # divide each input by its std
                        zca_whitening=False,  # apply ZCA whitening
                        rotation_range=0,  # randomly rotate images in the range (degrees, 0 to 180)
                        width_shift_range=0.1, # randomly shift images horizontally (fraction of total width)
                        height_shift_range=0.1, # randomly shift images vertically (fraction of total height)
                        horizontal_flip=True,  # randomly flip images
                        vertical_flip=False)  # randomly flip images

                    # Compute quantities required for featurewise normalization
                    # (std, mean, and principal components if ZCA whitening is applied).
                    datagen.fit(x_batch)

                    # Fit the model on the batches generated by datagen.flow().
                    history = self.model.fit_generator(
                        datagen.flow(x_batch, y_batch, batch_size=self.batch_size),
                        steps_per_epoch=x_batch.shape[0] // self.batch_size,
                        validation_data=(x_tbatch, y_tbatch),
                        epochs=self.epoch, verbose=1, max_q_size=100,
                        callbacks=[self.lr_reducer, self.early_stopper, self.csv_logger])

                self.loss += history.history["loss"][len(history.history["loss"])-1]
                self.acc += history.history["acc"][len(history.history["acc"])-1]
                self.val_loss += history.history["val_loss"][len(history.history["val_loss"])-1]
                self.val_acc += history.history["val_acc"][len(history.history["val_acc"])-1]

                while_cnt += 1
                input_data.next()

            if while_cnt > 0:
                self.loss =self.loss/while_cnt
                self.acc = self.acc / while_cnt
                self.val_loss = self.val_loss / while_cnt
                self.val_acc = self.val_acc / while_cnt

        except Exception as e:
            logging.info("Error[400] ..............................................")
            logging.info(e)

    def run(self, conf_data):
        '''
        Train run init
        :param conf_data: 
        :return: 
        '''
        try :
            logging.info("run NeuralNetNodeImage Train")
            # Common Start #############################################################################################
            # init value
            self = NeuralNetNode()._init_node_parm(self, conf_data)

            # netconf
            self.netconf = WorkFlowNetConf().get_view_obj(self.node_id)

            # dataconf & get data
            input_data, self.dataconf = self.get_input_data(self.feed_node, self.cls_pool, self.train_feed_name)
            test_data, self.dataconf_eval = self.get_input_data(self.feed_node, self.cls_pool, self.eval_feed_name)
            # Common End ###############################################################################################

            # Label Setup (1: HDF label row)
            self.labels, self.labels_cnt = self._get_netconf_labels(input_data, 1)

            # get model
            self.channel = self.dataconf["preprocess"]["channel"]
            self.x_size = self.dataconf["preprocess"]["x_size"]
            self.y_size = self.dataconf["preprocess"]["y_size"]

            self.keras_get_model()

            # Train
            self.train_cnt = self.netconf["param"]["traincnt"]
            self.batch_size = self.netconf["param"]["batch_size"]
            for i in range(self.train_cnt):
                # Train
                self.train_run(input_data, test_data)

                # Model Save :  _init_node_parm : self.save_path
                keras.models.save_model(self.model, self.save_path)

                # Acc Loss Save : _init_node_parm : self.acc_loss_result
                self.set_acc_loss_result(self.acc_loss_result, self.loss, self.acc, self.val_loss, self.val_acc)

                # Eval & Result Save
                self.eval(self.node_id, self.conf_data, test_data, None)

                # Eval Result Print
                self.eval_print(self.eval_data)
            return None
        except Exception as e :
            logging.info("===Error on Train  : {0}".format(e))

    ####################################################################################################################
    def eval(self, node_id, conf_data, data=None, result=None):
        '''
        eval run init
        :param node_id: 
        :param conf_data: 
        :param data: 
        :param result: 
        :return: 
        '''
        try :
            logging.info("run NeuralNetNodeImage eval")

            pred_cnt = self.netconf["param"]["predictcnt"]
            eval_type = self.netconf["config"]["eval_type"]

            # eval result
            config = {"type": eval_type, "labels": self.labels,
                      "nn_id": self.nn_id,
                      "nn_wf_ver_id": self.nn_wf_ver_id, "nn_batch_ver_id": self.train_batch}
            self.eval_data = TrainSummaryInfo(conf=config)

            if data is None:
                return self.eval_data

            data.reset_pointer()

            while (data.has_next()):
                data_set = data[0:data.data_size()]
                x_batch = self.get_convert_img_x(data_set[0], self.x_size, self.y_size, self.channel)  # img_data_batch
                logits = self.model.predict(x_batch)

                y_batch = self.get_convert_img_y_eval(data_set[1])

                for i in range(len(logits)):
                    true_name = y_batch[i]

                    logit = []
                    logit.append(logits[i])
                    retrun_data = self.set_predict_return_cnn_img(self.labels, logit, pred_cnt)
                    pred_name = retrun_data["key"]
                    #예측값이 배열로 넘어온다 한개라도 맞으면참
                    t_pred_name = pred_name[0]
                    for i in pred_name:
                        if i == true_name:
                            t_pred_name = i

                    # eval result
                    self.eval_data.set_result_info(true_name, t_pred_name)

                data.next()

            # eval result
            TrainSummaryInfo.save_result_info(self, self.eval_data)

            return self.eval_data

        except Exception as e :
            logging.info("===Error on Eval  : {0}".format(e))

    ####################################################################################################################
    def predict(self, node_id, filelist):
        '''
        predict
        :param node_id: 
        :param filelist: 
        :return: 
        '''
        logging.info("run NeuralNetNodeCnn Predict")
        self.node_id = node_id
        self._init_value()
        # net, data config setup
        data_node_name = self._get_backward_node_with_type(node_id, 'data')
        dataconf = WorkFlowNetConf().get_view_obj(data_node_name[0])
        netconf = WorkFlowNetConf().get_view_obj(self.node_id)
        self.netconf = netconf
        self._set_netconf_parm()
        self._set_dataconf_parm(dataconf)

        # data shape change MultiValuDict -> nd array
        filename_arr, filedata_arr = self.change_predict_fileList(filelist, dataconf)

        # get unique key
        self.load_batch = self.get_active_batch(self.node_id)
        unique_key = '_'.join([node_id, self.load_batch])

        logging.info("getModelPath:"+self.model_path + "/" + self.load_batch+self.file_end)

        ## create tensorflow graph
        if (NeuralNetModel.dict.get(unique_key)):
            self = NeuralNetModel.dict.get(unique_key)
            graph = NeuralNetModel.graph.get(unique_key)
        else:
            self.get_model_resnet()

            NeuralNetModel.dict[unique_key] = self
            NeuralNetModel.graph[unique_key] = tf.get_default_graph()
            graph = tf.get_default_graph()

        pred_return_data = {}
        for i in range(len(filename_arr)):
            file_name = filename_arr[i]
            file_data = filedata_arr[i]

            try:
                logits = self.model.predict(file_data)
            except Exception as e:
                self.get_model_resnet()

                NeuralNetModel.dict[unique_key] = self
                NeuralNetModel.graph[unique_key] = tf.get_default_graph()
                graph = tf.get_default_graph()
                logits = self.model.predict(file_data)

            labels = self.netconf["labels"]
            pred_cnt = self.netconf["param"]["predictcnt"]
            retrun_data = self.set_predict_return_cnn_img(labels, logits, pred_cnt)
            pred_return_data[file_name] = retrun_data
            logging.info("Return Data.......................................")
            logging.info(pred_return_data)

        return pred_return_data