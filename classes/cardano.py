import configparser
import uuid
import subprocess
import os
import sys
import json


config = configparser.ConfigParser()
config.read('config.ini')

bech32path = config['DEFAULT']['bech32Path']
cardanoSocketPath = config['DEFAULT']['cardanoSocketPath']

os.environ["CARDANO_NODE_SOCKET_PATH"] = str(cardanoSocketPath)


def generateKey(account,address, txBuilder):
    with open(config['DEFAULT']['mnemonic']) as f:
        mnemonic = f.readlines()[0].replace('\n','')
    
    commands = []
    commands.append("echo")
    commands.append("{}".format(mnemonic))
    ps = subprocess.Popen(commands, stdout=subprocess.PIPE)
    commands = []
    commands.append("cardano-address")    
    commands.append("key")    
    commands.append("from-recovery-phrase")    
    commands.append("Shelley")    
    output = subprocess.check_output(commands, stdin=ps.stdout)
    ps.wait()
    root_key = output.decode("utf-8")

    if root_key.startswith("root_xsk1") and len(root_key)>160:
        print(root_key)
        commands = []
        commands.append("echo")
        commands.append(root_key)
        ps = subprocess.Popen(commands, stdout=subprocess.PIPE)

        commands = []
        commands.append("cardano-address")
        commands.append("key")
        commands.append("child")
        commands.append("1852H/1815H/0H/{}/{}".format(account, address))
        output = subprocess.check_output(commands, stdin=ps.stdout)
        ps.wait()
        payment_skey = output.decode("utf-8")
        if payment_skey.startswith("addr_xs") and len(payment_skey)>160:
            print(payment_skey)
            print(os.environ["CARDANO_NODE_SOCKET_PATH"])

            commands = []
            commands.append("echo")
            commands.append(payment_skey)
            ps = subprocess.Popen(commands, stdout=subprocess.PIPE)

            commands = []
            commands.append("cardano-address")
            commands.append("key")
            commands.append("public")
            commands.append("--with-chain-code")
            output = subprocess.check_output(commands, stdin=ps.stdout)
            ps.wait()


            payment_vkey = output.decode("utf-8")
            if payment_vkey.startswith("addr_xvk1") and len(payment_vkey) > 110:
                try:
                    print(payment_vkey)
                    commands = []
                    commands.append("echo")
                    commands.append(payment_skey)
                    ps = subprocess.Popen(commands, stdout=subprocess.PIPE)
                    

                    commands = []
                    commands.append(bech32path)
                    p2 = subprocess.check_output(commands, stdin=ps.stdout)
                    ps.wait()

                    bech32 = p2.decode('utf-8').replace('\n','')
                    print("bech32: "+bech32 )

                    commands = []
                    commands.append("echo")
                    commands.append(bech32)
                    ps3 = subprocess.Popen(commands, stdout=subprocess.PIPE)

                    commands = []
                    commands.append("cut")
                    commands.append("-b")
                    commands.append("-128")
                    ps4 = subprocess.check_output(commands, stdin=ps3.stdout)
                    ps3.wait()

                    private = ps4.decode('utf-8').replace('\n','')

                    commands = []
                    commands.append("echo")
                    commands.append(payment_vkey)
                    ps5 = subprocess.Popen(commands, stdout=subprocess.PIPE)
                    

                    commands = []
                    commands.append(bech32path)
                    p6 = subprocess.check_output(commands, stdin=ps5.stdout)
                    ps5.wait()

                    public = p6.decode('utf-8').replace('\n','')



                    cbor_key = "5880{}{}".format(private, public).replace('\n','')
                    json_body = '{"type": "PaymentExtendedSigningKeyShelley_ed25519_bip32","description": "Payment Signing Key","cborHex": "'+str(cbor_key)+'"}'
                    parsed = json.loads(json_body)

                    json_string  = json.dumps(parsed, indent=4, sort_keys=False)
                    print(json_string)

                    f = open("files/{}.skey".format(txBuilder.uuid), "w")
                    f.write(json_string)
                    f.close()


                #( cat $DIR.payment.xprv | bech32 | cut -b -128 )$( cat $DIR.payment.xpub | bech32
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)    
                    pass


class Cardano:
    def __init__(self, network="testnet"):
        if network=="testnet":
            self.network_magic = "--testnet-magic 1097911063".split(" ")
        else:
            self.network_magic = "--mainnet".split(" ")


class TxInput:
    def __init__(self, hash, index):
        self.hash = hash
        self.index = index

class TxOutput:
    def __init__(self, recipient, ada_amount):
        self.recipient = recipient
        self.ada_amount = ada_amount

class TransactionBuilder:
    def __init__(self, type='build-raw'):
        self.commands = []
        self.inputs = []
        self.outputs = []
        self.witnesses = []
        self.type = type
        self.fee = 0
        self.uuid = uuid.uuid4().hex
        print("Creating new TX: {}".format(self.uuid))


    def add_input(txBuilder, hash, index):
        txBuilder.commands.append('--tx-in')
        txBuilder.commands.append('{}#{}'.format(hash, index))
        input = TxInput(hash, index)
        txBuilder.witnesses.append("lalala")
        txBuilder.inputs.append(input)
        print("added input {}#{}".format(hash, index))

    def add_output(txBuilder, recipient, ada_amount):
        txBuilder.commands.append('--tx-out')
        txBuilder.commands.append('{}+{}'.format(recipient, ada_amount))
        output = TxInput(recipient, ada_amount)
        txBuilder.inputs.append(output)
        print("added output {} ->{}".format(recipient, ada_amount))
    
    def dummy(txBuilder):
        commands = []
        commands.append(config['DEFAULT']['cardanoCliPath'])
        commands.append("transaction")
        commands.append(txBuilder.type)
        commands.append("--fee")
        commands.append(str(txBuilder.fee))
        for input in txBuilder.inputs:
            commands.append("--tx-in")
            commands.append("{}#{}".format(input.hash, input.index))
        for output in txBuilder.outputs:
            commands.append("--tx-out")
            commands.append("{}+{}".format(output.recipient, output.ada_amount))
        commands.append('--out-file')
        commands.append('files/{}-dummy-tx.raw'.format(txBuilder.uuid))

        try:
            result = subprocess.check_output(commands)
        except FileNotFoundError:
            print("We are unable to find your cardano-cli, please configure in config.ini")

    def estimate_fees(txBuilder, network):
        commands = []
        commands.append(config['DEFAULT']['CardanoCliPath'])
        commands.append("transaction")        
        commands.append("calculate-min-fee")        
        commands.append("--tx-body-file")        
        commands.append('files/{}-dummy-tx.raw'.format(txBuilder.uuid))        
        commands.append("--tx-in-count")        
        commands.append(str(len(txBuilder.inputs)))
        commands.append("--tx-out-count")        
        commands.append(str(len(txBuilder.outputs)))
        commands.append("--witness-count")        
        commands.append(str(len(txBuilder.witnesses)))
        for n in network.network_magic:
            commands.append(n) 
        commands.append("--protocol-params-file")
        commands.append(config['DEFAULT']['protocolParams'])
        fee = subprocess.check_output(commands)
        txBuilder.fee = int(fee.decode("utf-8").split(" ")[0])

    def finalize_tx(txBuilder):
        commands = []
        commands.append(config['DEFAULT']['cardanoCliPath'])
        commands.append("transaction")
        commands.append(txBuilder.type)
        commands.append("--fee")
        commands.append(str(txBuilder.fee))
        for input in txBuilder.inputs:
            commands.append("--tx-in")
            commands.append("{}#{}".format(input.hash, input.index))
        for output in txBuilder.outputs:
            commands.append("--tx-out")
            commands.append("{}+{}".format(output.recipient, output.ada_amount))
        commands.append('--out-file')
        commands.append('files/{}-final-tx.raw'.format(txBuilder.uuid))

        try:
            result = subprocess.check_output(commands)
        except FileNotFoundError:
            print("We are unable to find your cardano-cli, please configure in config.ini")

    def sign_tx(txBuilder, network):
        commands = []
        commands.append(config['DEFAULT']['cardanoCliPath'])
        commands.append("transaction")
        commands.append("sign")
        commands.append("--signing-key-file")
        generateKey(0,0, txBuilder)
        commands.append("files/{}.skey".format(txBuilder.uuid))
        for n in network.network_magic:
            commands.append(n) 
        commands.append("--tx-body-file")
        commands.append("files/{}-final-tx.raw".format(txBuilder.uuid))
        commands.append("--out-file")
        commands.append("files/{}-tx.signed".format(txBuilder.uuid))

        try:
            result = subprocess.check_output(commands)
        except FileNotFoundError:
            print("We are unable to find your cardano-cli, please configure in config.ini")

    def submit_tx(txBuilder):
        print("submitting")
        try:
            os.remove('files/{}-dummy-tx.raw'.format(txBuilder.uuid))
            os.remove('files/{}-final-tx.raw'.format(txBuilder.uuid))
            os.remove('files/{}-tx.signed'.format(txBuilder.uuid))
            os.remove('files/{}.skey'.format(txBuilder.uuid))
        except FileNotFoundError:
            pass


