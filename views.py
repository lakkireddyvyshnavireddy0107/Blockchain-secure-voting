from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
import os
import json
from web3 import Web3, HTTPProvider
from django.core.files.storage import FileSystemStorage
import os
from datetime import date # Import your local encrypt function with an alias
from ecies.utils import generate_eth_key, generate_key
from ecies import encrypt , decrypt   # Import ECIES encrypt and decrypt with aliases
from hashlib import sha256
import base64
global username
global contract, web3
global usersList, partyList, voteList

#function to generate public and private keys for ECC algorithm
def ECCGenerateKeys():
    if os.path.exists("pvt.key"):
        with open("pvt.key", 'rb') as f:
            private_key = f.read()
        f.close()
        with open("pri.key", 'rb') as f:
            public_key = f.read()
        f.close()
        private_key = private_key.decode()
        public_key = public_key.decode()
    else:
        secret_key = generate_eth_key()
        private_key = secret_key.to_hex()  # hex string
        public_key = secret_key.public_key.to_hex()
        with open("pvt.key", 'wb') as f:
            f.write(private_key.encode())
        f.close()
        with open("pri.key", 'wb') as f:
            f.write(public_key.encode())
        f.close()
    return private_key, public_key

#ECC will encrypt data using plain text adn public key
def ECCEncrypt(plainText, public_key):
    ecc_encrypt = encrypt(public_key, plainText)
    return ecc_encrypt

#ECC will decrypt data using private key and encrypted text
def ECCDecrypt(encrypt, private_key):
    ecc_decrypt = decrypt(private_key, encrypt)
    return ecc_decrypt

#function to call contract
def getContract():
    global contract, web3
    blockchain_address = 'http://127.0.0.1:9545'
    web3 = Web3(HTTPProvider(blockchain_address))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    compiled_contract_path = 'Voting.json' #voting contract file
    deployed_contract_address = '0x25Dadc623A5A96CfC4791D2923DC2c888f761a52' #contract address==================
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)  # load contract info as JSON
        contract_abi = contract_json['abi']  # fetch contract's abi - necessary to call its functions
    file.close()
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
getContract()

def getUsersList():
    global usersList, contract
    usersList = []
    count = contract.functions.getUserCount().call()
    for i in range(0, count):
        user = contract.functions.getUsername(i).call()
        password = contract.functions.getPassword(i).call()
        email = contract.functions.getEmail(i).call()
        aadhar = contract.functions.getUserAadhar(i).call()
        usersList.append([user, password, email, aadhar])

def getPartyList():
    global partyList, contract
    partyList = []
    count = contract.functions.getPartyCount().call()
    for i in range(0, count):
        cname = contract.functions.getCandidateName(i).call()
        pname = contract.functions.getPartyName(i).call()
        area = contract.functions.getArea(i).call()
        symbol = contract.functions.getSymbol(i).call()
        aadhar = contract.functions.getCandidateAadhar(i).call()
        partyList.append([cname, pname, area, symbol, aadhar])

def getVoteList():
    global voteList, contract
    voteList = []
    count = contract.functions.getVotingCount().call()
    for i in range(0, count):
        user = contract.functions.getUser(i).call()
        party = contract.functions.getParty(i).call()
        dd = contract.functions.getDate(i).call()
        candidate = contract.functions.getCandidate(i).call()
        voteList.append([user, party, dd, candidate])

getUsersList()
getPartyList()        
getVoteList()        

def alreadyCastVote(candidate):
    global voteList
    count = 0
    for i in range(len(voteList)):
        vl = voteList[i]
        if vl[0] == candidate:
            count = 1
    return count

def FinishVote(request):
    if request.method == 'GET':
        global username, voteList
        cname = request.GET.get('cname', False)
        pname = request.GET.get('pname', False)
        voter = ''
        today = date.today()
        status = 'Your vote casted to '+cname
        msg = contract.functions.createVote(username, pname, str(today), cname).transact()
        web3.eth.waitForTransactionReceipt(msg)
        voteList.append([username, pname, str(today), cname])
        context= {'data':'<font size=3 color=white>Your Vote Accepted for Candidate '+cname}
        return render(request, 'UserScreen.html', context)

def getOutput():
    global partyList
    output = '<table border=1 align=center>'
    output+='<tr><th><font size=3 color=white>Candidate Name</font></th>'
    output+='<th><font size=3 color=white>Party Name</font></th>'
    output+='<th><font size=3 color=white>Area Name</font></th>'
    output+='<th><font size=3 color=white>Image</font></th>'
    output+='<th><font size=3 color=white>Cast Vote Here</font></th></tr>'
    for i in range(len(partyList)):
        pl = partyList[i]
        output+='<tr><td><font size=3 color=white>'+pl[0]+'</font></td>'
        output+='<td><font size=3 color=white>'+pl[1]+'</font></td>'
        output+='<td><font size=3 color=white>'+pl[2]+'</font></td>'
        output+='<td><img src="/static/parties/'+pl[3]+'" width=200 height=200></img></td>'
        output+='<td><a href="ConfirmVote?cname='+pl[0]+'&pname='+pl[1]+'"><font size=3 color=white>Click Here</font></a></td></tr>'
    output+="</table><br/><br/><br/><br/><br/><br/>"        
    return output

def UserScreen(request):
    if request.method == 'GET':
        context= {'data':"Click on 'Cast your Vote' link to view list again"}
        return render(request, 'UserScreen.html', context)

def ConfirmVote(request):
    if request.method == 'GET':
        global username
        cname = request.GET.get('cname', False)
        pname = request.GET.get('pname', False)
        print(cname)
        print(pname)
        output = '<table border=1 align=center>'
        output+='<tr>'
        output+='<th><font size=3 color=white>Click YES to Confirm or NO to Cancel</font></th></tr>'
        output+='<tr><td><a href="FinishVote?cname='+cname+'&pname='+pname+'"><font size=3 color=white>YES</font></a>&nbsp;&nbsp;'
        output+='<a href="UserScreen"><font size=3 color=white>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;NO</font></a></td></tr>'
        output+="</table><br/><br/><br/><br/><br/><br/>"        
        context= {'data':output}
        return render(request, "UserScreen.html", context)

def Vote(request):
    if request.method == 'GET':
        global username
        dd = ""
        status = ""
        page = 'Vote.html'
        if os.path.exists("EVotingApp/static/dd.txt"):
            with open("EVotingApp/static/dd.txt", "rb") as file:
                value = file.read()
            file.close()
            dd = value.decode()
            arr = dd.split(" ")
            arr = arr[0]
            arr = arr.split("-")
            if len(arr[1].strip()) == 1:
                arr[1] = "0"+arr[1].strip()
            today = str(date.today())
            current_arr = today.split("-")
            if current_arr[0] == arr[2] and current_arr[1] == arr[1] and current_arr[2] == arr[0]:
                count = alreadyCastVote(username)
                if count == 0:
                    status = getOutput()
                else:
                    status = "You already casted vote"
            else:
                status = "Today is not an election date.<br/>Election is on "+dd
                
        else:
            status = "Election date not yet publish.<br/>Election date you can see in your home page after login"
        context= {'data':status}
        return render(request, page, context)         
        

def getVoteCount(cname, pname):
    global voteList
    count = 0
    for i in range(len(voteList)):
        vl = voteList[i]
        if vl[1] == pname and vl[3] == cname:
            count += 1
    return count        

def ViewCount(request):
    if request.method == 'GET':
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=white>Candidate Name</font></th>'
        output+='<th><font size=3 color=white>Party Name</font></th>'
        output+='<th><font size=3 color=white>Area Name</font></th>'
        output+='<th><font size=3 color=white>Image</font></th>'
        output+='<th><font size=3 color=white>Vote Count</font></th>'
        for i in range(len(partyList)):
            pl = partyList[i]
            count = getVoteCount(pl[0], pl[1])
            output+='<tr><td><font size=3 color=white>'+pl[0]+'</font></td>'
            output+='<td><font size=3 color=white>'+pl[1]+'</font></td>'
            output+='<td><font size=3 color=white>'+pl[2]+'</font></td>'
            output+='<td><img src="/static/parties/'+pl[3]+'" width=200 height=200></img></td>'
            output+='<td><font size=3 color=white>'+str(count)+'</font></td></tr>'
        output+="</table><br/><br/><br/><br/><br/><br/>"        
        context= {'data':output}
        return render(request, 'ViewResult.html', context)

def ViewUserResult(request):
    if request.method == 'GET':
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=white>Current Winner Name</font></th>'
        output+='<th><font size=3 color=white>Vote Count</font></th></tr>'
        name = ""
        total = 0
        for i in range(len(partyList)):
            pl = partyList[i]
            count = getVoteCount(pl[0], pl[1])
            if count > total:
                total = count
                name = pl[0]
        if total > 0:
            output+='<tr><td><font size=3 color=white>Winner = '+name+'</font></td>'
            output+='<td><font size=3 color=white>Total Votes Received = '+str(total)+'</font></tr>'
        else:
            output+='<tr><td><font size=3 color=white>Result Not Yet Declared</font></td>'
            output+='<td><font size=3 color=white>0</font></tr>'
        output+="</table><br/><br/><br/><br/><br/><br/>"        
        context= {'data':output}
        return render(request, 'UserScreen.html', context)    

def AddElectionDate(request):
    if request.method == 'GET':
       return render(request, 'AddElectionDate.html', {})

def AddElectionDateAction(request):
    if request.method == 'POST':
        dd = request.POST.get('t1', False)
        with open("EVotingApp/static/dd.txt", "wb") as file:
            dd = dd.encode()
            file.write(dd)
        file.close()
        context= {'data': "Election date & time details added"}
        return render(request, "AddElectionDate.html", context)

def AddVoterAction(request):
    if request.method == 'POST':
      global username, password, contact, email, address, usersList
      username = request.POST.get('t1', False)
      password = request.POST.get('t2', False)
      contact = request.POST.get('t3', False)
      email = request.POST.get('t4', False)
      address = request.POST.get('t5', False)
      aadhar = request.POST.get('t6', False)
      status = "none"
      for i in range(len(usersList)):
          ul = usersList[i]
          if username == ul[0]:
              status = "exists"
              break
      if status == "none":
          private_key, public_key = ECCGenerateKeys()
          encrypted_aadhar = ECCEncrypt(aadhar.encode(), public_key)#applying second encrypt as double encryption
          sha_code = sha256(encrypted_aadhar).hexdigest()
          encrypted_aadhar = base64.b64encode(encrypted_aadhar).decode()
          msg = contract.functions.createUser(username, email, password, contact, address, encrypted_aadhar+" "+sha_code).transact()
          status = 'User Details added to Blockchain<br/>Aadhar SHA256 Authenticated Code : '+sha_code+'<br/>Encrypted ECC Aadhar '+encrypted_aadhar+'<br/><br/>'
          status += str(web3.eth.waitForTransactionReceipt(msg))
          usersList.append([username, password, email, encrypted_aadhar+" "+sha_code])
      else:
          status = "Username already exists"
      context= {'data': status}
      return render(request, "AddVoter.html", context)

def AddVoter(request):
    if request.method == 'GET':
       return render(request, 'AddVoter.html', {})        

def AddCandidateAction(request):
    if request.method == 'POST':
        global partyList
        cname = request.POST.get('t1', False)
        pname = request.POST.get('t2', False)
        area = request.POST.get('t3', False)
        aadhar = request.POST.get('t5', False)
        myfile = request.FILES['t4']
        imagename = request.FILES['t4'].name
        status = "none"
        page = "AddCandidate.html"
        for i in range(len(partyList)):
            pl = partyList[i]
            if cname == pl[0] and pname == pl[1]:
                status = "Candidate & Party Name Already Exists"
                break
        if status == "none":
            if os.path.exists('EVotingApp/static/parties/'+imagename):
                os.remove('EVotingApp/static/parties/'+imagename)
            fs = FileSystemStorage()
            filename = fs.save('EVotingApp/static/parties/'+imagename, myfile)
            private_key, public_key = ECCGenerateKeys()
            encrypted_aadhar = ECCEncrypt(aadhar.encode(), public_key)#applying second encrypt as double encryption
            sha_code = sha256(encrypted_aadhar).hexdigest()
            encrypted_aadhar = base64.b64encode(encrypted_aadhar).decode()
            status = 'Candidate details added to Blockchain<br/>Aadhar SHA256 Authenticated Code : '+sha_code+'<br/>Encrypted ECC Aadhar '+encrypted_aadhar+'<br/><br/>'
            msg = contract.functions.createParty(cname, pname, area, imagename, encrypted_aadhar+" "+sha_code).transact()
            status += str(web3.eth.waitForTransactionReceipt(msg))
            partyList.append([cname, pname, area, imagename, encrypted_aadhar+" "+sha_code])
        context= {'data': status}
        return render(request, page, context)        

def UserLogin(request):
    if request.method == 'POST':
        global username, contract, usersList
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        status = "User.html"
        output = 'Invalid login details'
        for i in range(len(usersList)):
            ulist = usersList[i]
            user1 = ulist[0]
            pass1 = ulist[1]
            if user1 == username and pass1 == password:
                dd = ""
                if os.path.exists("EVotingApp/static/dd.txt"):
                    with open("EVotingApp/static/dd.txt", "rb") as file:
                        value = file.read()
                    file.close()
                    dd = "Election Date & Time = "+str(value.decode())
                status = "UserScreen.html"
                output = 'Welcome '+username+"<br/>"+dd
                break        
        context= {'data':output}
        return render(request, status, context)        

def AdminLogin(request):
    if request.method == 'POST':
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        if username == 'admin' and password == 'admin':
            context= {'data':'Welcome Admin'}
            return render(request, "AdminScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'Admin.html', context)

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Admin(request):
    if request.method == 'GET':
       return render(request, 'Admin.html', {})

def User(request):
    if request.method == 'GET':
       return render(request, 'User.html', {})    

def AddCandidate(request):
    if request.method == 'GET':
       return render(request, 'AddCandidate.html', {})



    
