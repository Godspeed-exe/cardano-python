from classes.cardano import *
import sys




try:
    network = Cardano(network="testnet")

    newTx = TransactionBuilder()

    newTx.add_input('0a385129cafdf6229c51d6d8154b7dfff2e68981720cceb7b8a906f782e909b0', 0)
    newTx.add_input('0a385129cafdf6229c51d6d8154b7dfff2e68981720cceb7b8a906f782e909b0', 0)
    newTx.add_input('0a385129cafdf6229c51d6d8154b7dfff2e68981720cceb7b8a906f782e909b0', 0)
    newTx.add_input('0a385129cafdf6229c51d6d8154b7dfff2e68981720cceb7b8a906f782e909b0', 0)
    newTx.add_input('0a385129cafdf6229c51d6d8154b7dfff2e68981720cceb7b8a906f782e909b0', 0)
    newTx.add_input('0a385129cafdf6229c51d6d8154b7dfff2e68981720cceb7b8a906f782e909b0', 0)
    newTx.dummy()
    print("fee before: {}".format(newTx.fee))
    newTx.estimate_fees(network)
    print("fee after: {}".format(newTx.fee))
    newTx.finalize_tx()
    newTx.sign_tx(network)
    newTx.submit_tx()

except Exception as e:
    print("Error: {}".format(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)    