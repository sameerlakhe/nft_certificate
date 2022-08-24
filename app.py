# ------------------------------------------------------------------------------
# Imports
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from datetime import date
import os
import json
from web3 import Web3
from pathlib import Path
from dotenv import load_dotenv
import requests
from cryptography.fernet import Fernet

# ------------------------------------------------------------------------------
# Flask App

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


load_dotenv()

# Create a W3 Connection
w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URI")))

# Set up Pinata Headers
json_headers = {
        "Content-Type":"application/json",
        "pinata_api_key": os.getenv("PINATA_API_KEY"),
        "pinata_secret_api_key": os.getenv("PINATA_SECRET_API_KEY")
}

file_headers = {
        "pinata_api_key": os.getenv("PINATA_API_KEY"),
        "pinata_secret_api_key": os.getenv("PINATA_SECRET_API_KEY")
}


@app.route('/mint_nft', methods=['POST'])
def mint_nft():
    #try:
        pic = request.files["pic"]
        if not pic:
            return 'No pic uploaded', 400

        file_name = secure_filename(pic.filename)
        mimetype = pic.mimetype

        form_data = request.form
        student_name = form_data['student_name']
        grade = form_data['grade']
        description = form_data['description']
        wallet_address = form_data['wallet_address']

        pic.save(os.path.join("./uploads", file_name))
        pic.seek(0)
        
        content = pic.read()
        #content = str(content)
       
        # return render_template('index.html')
        minter ="University of Toronto"
        
        result = generate_nft(student_name,content,grade,description,wallet_address,minter)
        return result, 200
    #except  Exception as e:
        #print("something went wrong",e)
        #return 'IIssue minting NFT', 500
    #except:
     #   print("Unexpected error:", sys.exc_info()[0])



def convert_data_to_json(content):
    data = {"pinataOptions":{"cidVersion":1}, 
            "pinataContent":content }
    return json.dumps(data)

def pin_file_to_ipfs(data):
    r = requests.post("https://api.pinata.cloud/pinning/pinFileToIPFS",
                      files={'file':data},
                      headers= file_headers)
    print(r.json())
    ipfs_hash = r.json()["IpfsHash"]
    return ipfs_hash

def pin_json_to_ipfs(json):
    r = requests.post("https://api.pinata.cloud/pinning/pinJSONToIPFS",
                      data=json,
                      headers= json_headers)
    print(r.json())
    ipfs_hash = r.json()["IpfsHash"]
    return ipfs_hash

def pin_nft(nft_data, file,**kwargs):
    # Pin certificate picture to IPFS
    #ipfs_file_hash = pin_file_to_ipfs(file.getvalue())
    ipfs_file_hash = pin_file_to_ipfs(file)

    # Build our NFT Token JSON
    token_json = {
       "nft_data": nft_data,
       "image": f"ipfs.io/ipfs/{ipfs_file_hash}"
    }

    # Add extra attributes if any passed in
    token_json.update(kwargs.items())

    # Add to pinata json to be uploaded to Pinata
    json_data = convert_data_to_json(token_json)

    # Pin the real NFT Token JSON
    json_ipfs_hash = pin_json_to_ipfs(json_data)

    return json_ipfs_hash, token_json


######################################################################
## Load the contract
######################################################################

def load_contract():
    with open(Path("./contracts/compiled/Certificate_abi.json")) as file:
        picture_abi = json.load(file)

    contract_address = os.getenv("SMART_CONTRACT_ADDRESS")

    beach_contract = w3.eth.contract(address=contract_address,
                    abi=picture_abi)

    return beach_contract    





def generate_nft(name,file,grade,description,wallet_address,minter):
    contract = load_contract()
    nft_data ={}
    nft_data['name'] = name;
    nft_data['grade'] = grade;
    nft_data['description'] = description;
    nft_data['wallet_address'] = wallet_address;
    nft_data['minter'] = minter;

    nft_json_data = json.dumps(nft_data)
    print(nft_data)

    key = Fernet.generate_key()
    fernet = Fernet(key)
    
    encrypted_data = fernet.encrypt(nft_json_data.encode())
    
    print(encrypted_data)
    encrypted_data = str(encrypted_data)
    
    nft_ipfs_hash,token_json = pin_nft(nft_json_data,file,encrypted_data=encrypted_data)

    nft_uri = f"ipfs.io/ipfs/{nft_ipfs_hash}"
 
    # THIS ONLY WORKS IN GANACHE
    #tx_hash = contract.functions.registerPicture(account, name, artist, image_details, nft_uri).transact({'from':account,'gas':1000000})
    wallet_address = Web3.toChecksumAddress(wallet_address)
    print(wallet_address)

    tx_hash = contract.functions.registerCertificate(wallet_address, name, grade, description, nft_uri,minter,encrypted_data).transact({'from':wallet_address,'gas':1000000})

    # This generally works on the mainnet - Rinkeby, not so much
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)      

    complete_url= "https://"+nft_uri
    complete_ipfs_gateway_link = "https://"+token_json['image']
    print(complete_url)
    print(complete_ipfs_gateway_link)

    result ={}
    result['complete_url'] = complete_url
    result['complete_ipfs_gateway_link'] = complete_ipfs_gateway_link
    return result