from cluster.service.service_predict import PredictNet
from third_party.ngram.ngram_compare_mro import ThirdPartyNgram
from master.network.nn_common_manager import NNCommonManager

class PredictNetNgram(PredictNet):
    def run(self, type, nn_id, ver, parm):
        """
        run predict service
        1. get node id
        2. check json conf format
        3. run predict & return
        :param parm:
        :return:
        """
        if(self._valid_check(parm)) :
            if ver == 'active':
                condition = {'nn_id': nn_id}
                ver = NNCommonManager().get_nn_info(condition)[0]['nn_wf_ver_id']

            return ThirdPartyNgram().predict(type, nn_id, ver)

    def _valid_check(self, parm):
        return True