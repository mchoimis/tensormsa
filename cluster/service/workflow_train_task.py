from __future__ import absolute_import, unicode_literals
from celery import Task
import importlib


class WorkFlowTrainTask(Task):

    def run(self, source, *args, **kwargs):
        self.source = source

        self._exec_train(source.nn_id , source.wf_ver)


    def _exec_train(self, nn_id, wf_ver):
        """
        start train with predefined workflow process
        :param nn_id:
        :param wf_ver:
        :return:
        """
        # get next node id to run
        _node_id = self._get_next_node(nn_id, wf_ver)
        if(_node_id == None) :
            return
        # get node info (class name & class run config info)
        _cls, _cls_data = self._get_node_info(_node_id)
        # run node
        step_result = self._load_class(_cls).run(_cls_data)
        # run next
        self._exec_train(nn_id, wf_ver)


    def _get_next_node(self, nn_id, wf_ver):
        node_id = None
        return node_id

    def _get_node_info(self, node_id):
        _cls = None
        _cls_data = None
        return _cls, _cls_data

    def _get_module_name(self, type):
        if(type == 'DATA'):
            return "cluster.data"
        elif(type == 'NET'):
            return "cluster.neuralnet"
        elif(type == 'PRE'):
            return "cluster.preprocess"
        elif (type == 'CONF'):
            return "cluster.dataconfig"

    def _load_class(self, class_name, type):
        """
        return class with name
        :param module_name:
        :param class_name:
        :return: Class
        """
        module = importlib.import_module(self._get_module_name(type))
        LoadClass = getattr(module, class_name)
        return LoadClass()

    def _exec_node(self):
        return None

    def _stop_task(self):
        return None

    def _get_arranged_node_list(self):
        return None

    def _run_next_node(self):
        return None

    def _check_node_job_state(self):
        return None

    def _report_server_state(self):
        return None

    def _report_job_state(self):
        return None










