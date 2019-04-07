###########################################################################################
#
# Author: Mario Leonardo Salinas
# This library provides functions to:
#   . parse the SematicScholar corpus with a fuzzy search 
#     based upon the set of "Interesting Journals" (see Readme for dowload and credits)
#   . create the papers and authors' datasets
#   . read/write datasets   
#
# The usage is shwon from line 489 on.
#
###########################################################################################
from __future__ import division
import gzip
import time
import io
import string
from string import maketrans
import json
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import heapq

def export_partialJ(path, j_obj):
    with io.open(path, mode='w', encoding = 'utf8')  as f:
        i = 0
        l = len(j_obj)
        for j in j_obj:
            f.write(unicode(json.dumps(j)))
            f.write(unicode('\n'))

def import_partialJ(path):
    with io.open(path, mode='r', encoding = 'utf8')  as f:
        js = []
        for l in f:
            js.append(json.loads(l))
        return js

journals = import_partialJ("journals.txt")

exclude_words = set([
    'foreword',
    'preface',
    'editorial',
    'editorials'
    'acknowledgements'
])

exclude2 = set([
    'guest',
    'editor',
    'editors'
])

def contains_words(s):
    spl = s.split(" ")
    splt = set()
    sp = []
    for s in spl:
        try:
            sp.append(str(s))
        except Exception:
            continue;
    #print(sp)
    for s in sp:
        splt.add(s.translate(maketrans('',''),string.punctuation).lower())
    return (len(exclude_words & splt)>0 or len(exclude2 & splt)>=2);

def keep_goodP(papers):
    i = 0
    keep = []
    drop = []
    for p in papers:
        if (len(p['authors']) == 0) or (len(p['authors']) >= 15) or contains_words(p['title']):
            drop.append(p)
        else:
            keep.append(p)
        i += 1
    #print("Kept: "+str(len(keep))+" - Discarder: "+str(len(drop)))
    #print("Total papers: "+str(i))
    return [keep, drop]      



def start():
    print('START at: ' + str(time.ctime()))
def end():
    print('END at: ' + str(time.ctime()))
    
def LengthOfFile(f):
    currentPos=f.tell()
    f.seek(0, 2)          # move to end of file
    length = f.tell()     # get current position
    f.seek(currentPos, 0) # go back to where we started
    return length

############################
#   papersGraph functions  #
############################

def setAuthoring(authoring, authors, idP):
    for a in authors:
        heapq.heappush(authoring, (a, idP))
    return authoring

def getPaperSet(papers):
    pS = set()
    for p in papers:
        pS.add(p['id'])
    return pS

def setCitations(citations, idP, cIn, cOut, PIds, inTot, inInP, outTot, outInP):
    if len(cIn) > 0:
        for inc in cIn:
            inTot += 1
            if(inc in PIds):
                inInP += 1
                el = (inc, idP)
                if not(el in citations):
                    heapq.heappush(citations, el)
    if len(cOut) > 0:
        for outc in cOut:
            outTot += 1
            if(outc in PIds):
                outInP += 1
                el = (idP, outc)
                if not(el in citations):
                    heapq.heappush(citations, el)
    return citations,inTot, inInP, outTot, outInP

def getPaperSet(papers):
    pS = set()
    for p in papers:
        pS.add(p['id'])
    return pS

def getAuthorsSet(authors):
    authSet = set()
    if len(authors)>0:
        for auth in authors:
            idA = auth['ids'] 
            if len(idA)>0:
                authSet.add(idA[0])
    return authSet

def getPapersTestingJSON(papers, PIds):
    inTot = 0
    inInP = 0
    outTot = 0
    outInP = 0
    citations = []
    authoring = []
    papersJson = dict()
    added = 0
    i = 0
    l = len(papers)
    jN = ''
    j_id = ''
    v_id = ''
    venue = ''
    for p in papers:
        add = True
        try:
            idP = p['id']
            title = p['title']
            authorsId = getAuthorsSet(p['authors'])
            year = p['year']
        except Exception:
            add = False
            continue;
        try:
            jN = p['journalName']
            j_id = p['journalID']
        except Exception:
            continue;
        try:
            venue = p['venue']
            v_id = p['venueID']
        except Exception:
            continue;
        inC = set(p['inCitations'])
        outC = set(p['outCitations'])
        authoring = setAuthoring(authoring, authorsId, idP)
        inPrev = inTot
        outPrev = outInP
        citations, inTot, inInP, outTot, outInP = setCitations(citations, idP, inC, outC, PIds, inTot, inInP, outTot, outInP)
        i+=1
        if(add):
            papersJson[idP] = [title, year, jN, venue, authorsId, (inTot-inPrev), (outInP-outPrev), j_id, v_id]
        else:
            added = added+1
        if i % 1000 == 0:
            tm = time.asctime()
            tm = tm.split(' ')
            tm = tm[3]
            print('['+tm+'] Processed '+str(i)+' papers')
    print(str(len(papersJson))+' papers loaded, '+str(added)+' discarded')
    printInOutStats(inTot, inInP, outTot, outInP)
    return papersJson, authoring, citations

# "authoringLinks":[
#     {"source": "authId", "target": "paperId", "value": 1},the last no comma
# ],
# "citations":[
#     {"source": "paperId1", "target": "paperId2", "value": 1},the last no comma
# ]
#}
def writeCitations(cits, f):
    value = 5
    lim = len(cits)
    for i in range(0, lim):
        el = heapq.heappop(cits)
        source = el[0]
        target = el[1]
        cF = {'source':source, 'target':target, 'value':value}
        f.write(unicode(json.dumps(cF)))
        if i < (lim-1):
            f.write(unicode(', '))
    f.write(unicode(']} '))

def writeAuth(auth, f):
    lim = len(auth)
    for i in range(0, lim):
        el = heapq.heappop(auth)
        source = el[0]
        target = el[1]
        value = 5
        aF = {'source':source, 'target':target, 'value':value}
        f.write(unicode(json.dumps(aF)))
        if i < (lim-1):
            f.write(unicode(', '))
    f.write(unicode('], '))

def printInOutStats(inTot, inInP, outTot, outInP):
    print('Total inC = '+str(inTot)+' - inInP = '+str(inInP))
    print('Total outC = '+str(outTot)+' - outInP = '+str(outInP))    
       
def getP(path):
    P=[]
    with io.open(path, mode='r', encoding = 'utf8') as f:
        for l in f:
            P.append(json.loads(l))
    return P

def saveP(papers, path):
    with io.open(path, mode='w', encoding = 'utf8') as f:
        for p in papers:
            f.write(unicode(json.dumps(p)))
            f.write(unicode("\n"))

def papersTestingForSearchFile(path, pJSON, auth, cit):
    i = 0
    l = len(pJSON)
    with io.open(path, mode='w', encoding = 'utf8') as f:
        f.write(unicode('{"nodes": ['))
        for paper in pJSON:
            idP = paper
            p = pJSON[paper]
            authsIDs = []
            for a in p[4]:
                authsIDs.append(a)
            pF = {'id':idP, 'value':p[0], 'color':p[5], 'nOc':p[6], 'year':p[1], 'jN':p[2], 'venue':p[3], 'authsId': authsIDs, 'j_id':p[7], 'v_id':p[8]}
            f.write(unicode(json.dumps(pF)))
            if i < (l-1):
                f.write(unicode(', '))
            i+=1
        f.write(unicode('], '))
        f.write(unicode('"authoringLinks": ['))
        writeAuth(auth, f)
        f.write(unicode('"links": ['))
        writeCitations(cit, f)
    print('DONE.')
    
def getLastest(papers):
    tmp = []
    for p in papers:
        if p['year'] >= 2016:
            tmp.append(p)
    return tmp

def incr_count(jn, js):
    for i in range(len(js)):
        if (journals[i]['id'] == jn):
            js[i]['count'] += 1
            return js

def rebuild_journals():
    journals_new = []
    for i in range(len(journals)):
        j = journals[i]
        journals_new.append({'id':j['id'], 'name_list':j['name_list'], 'count':0})
    return journals_new
        

def fuzzy_search(path):
    add = 0
    scoreTot = 0
    fuzzyP = []
    read = 0
    i = 1
    journals_new = rebuild_journals()
    
    start()
    
    with gzip.open(path, 'rb') as f:
    #with io.open(path, mode = "r", encoding = 'utf-8') as f:
        for l in f:
            p = json.loads(l)
            jn = p['journalName']
            v = p['venue']
            score = 0
            p1 = p
            
            try:
                scoresj = dict({})
                scoresv = dict({})

                for j in journals:
                    if jn:
                        scoresj[j['id']] = process.extractOne(jn, j['name_list'], scorer=fuzz.token_sort_ratio)[1]
                    if v:
                        scoresv[j['id']] = process.extractOne(v, j['name_list'], scorer=fuzz.token_sort_ratio)[1]

                kj = max(scoresj, key=scoresj.get) if jn else None
                kv = max(scoresv, key=scoresv.get) if v else None
                
                scorej = scoresj[kj] if kj else None
                scorev = scoresv[kv] if kv else None
                
                score = max(scorej, scorev)
                 
                journals_new = incr_count(kj, journals_new) if kj and scorej > 80 else journals_new
                cond = kj and kv
                journals_new = incr_count(kv, journals_new) if (kv and scorev > 80)  and (not kj or (cond and not(kv == kj))) else journals_new

                p1['journalId'] = kj if kj else ''
                p1['venueId'] = kv if kv else ''
                    
            except Exception:
		      #print(Exception.message())
                continue;
        
            if score > 80:
                scoreTot += score
                fuzzyP.append(p1)
                add += 1
            
            if(i%50000==0):
                tm = time.asctime()
                print('['+tm+'] In '+str(path)+ ' processed '+str(i)+' papers - added '+str(add))
            
            i+=1
    avgScore = 0
    
    if add != 0:
        avgScore = scoreTot/add 
    end()
    print('In '+str(path)+' average score of fuzzy search: '+str(avgScore)+' - Passed: '+str(add))
    
    return keep_goodP(fuzzyP)[0], journals_new

############################
#  authorsGraph functions  #
############################

#function that writes the authors JSON file in a file in path
def authorsForSearchFile(path, authJson1):
    with io.open(path, mode='w', encoding = 'utf8')  as f:
        f.write(unicode('{"authors": ['))
        i = 0
        l = len(authJson1)
        for a in authJson1:
            idA = a
            a = authJson1[a]
            aF = {'id':idA, 'value':a[0], 'coAuthList':a[1], 'paperList':a[2], 'lastPub':a[3]}
            f.write(unicode(json.dumps(aF)))
            if i < l-1:
                f.write(unicode(', '))
            i+=1
        f.write(unicode(']}'))

# function that updates an authorDict entry 
# according to the employed model:
# {id, value(name) , coAuthList : [idACo, #pubs, lastYear, [papList]], paperIdList, lastPub : [year, idP] },
#           0              1                  0      1          2             2          3       0   1 
def updateCoAuth(auths, idA, aL, year, id_shared_pap):
    for a in aL:
        if a != idA:
            if not(a in auths[idA][1]):
                if a in auths:
                    #name = auths[a][0] [Redundancy removed:search for name by id]
                    auths[idA][1][a]=[1, year, [id_shared_pap]]
            else:
                auths[idA][1][a][0] += 1
                auths[idA][1][a][2].append(id_shared_pap)
                if auths[idA][1][a][1] < year:
                    auths[idA][1][a][1] = year

def addAuthId(authSet, authors):
    if len(authors)>0:
        for auth in authors:
            idA = auth['ids'] 
            if len(idA)>0:
                idA = idA[0]
                authSet.add(idA)
    return authSet
       
def getAuthsIdSetF(path):
    start()
    i = 1
    filePos = 0
    lenght = 0
    authSet = set([])
    with io.open(path, mode='r', encoding = 'utf8') as f1:
        lenght = LengthOfFile(f1)
        for line in f1:
            lln = len(line) + len('\n')
            filePos += lln
            r = json.loads(line)
            authors = r['authors']
            authSet = addAuthId(authSet, authors)
            if i % 100000 == 0:
                perc =(filePos*100)/(lenght) 
                perc = str(perc)
                perc = perc[0:5]
                tm = time.asctime()
                tm = tm.split(' ')
                tm = tm[3]
                print('['+tm+'] Processed '+str(perc)+' - '+str(i)+' papers - ')
            i+=1
    end()
    return authSet
 
def getAuthsIdSet(papers):
    start()
    authSet = set([])
    for r in papers:       
        authors = r['authors']
        authSet = addAuthId(authSet, authors)
    end()
    return authSet

def getAuthJson(papers):
    authJson = dict()
    for p in papers:
        authors = p['authors']
        for ap in authors:
            if ((len(ap['ids']) > 0) and (not(ap['ids'][0] in authJson))):
                name = ap['name']
                authJson[ap['ids'][0]] = [name, dict(), [], [0, '']]
    return authJson

def authorsJSONObj(papers, authJson1):
    l = len(papers)
    i=1
    start()
    for s in papers:
        paperAuths = set([])
        authors = s['authors']
        idP = s['id']
        try:
            year = s['year']
        except Exception:
            year = 0
            continue;
        for ap in authors:
            if ((len(ap['ids']) > 0) and (ap['ids'][0] in authJson1)):
                paperAuths.add(ap['ids'][0])
        for ap in authors:   
            if ((len(ap['ids']) > 0) and (ap['ids'][0] in authJson1)):
                idA = ap['ids'][0]
                updateCoAuth(authJson1, idA, paperAuths, year, idP)
                authJson1[idA][2].append(idP)
                if year > authJson1[idA][3][0]:
                    authJson1[idA][3] = [year, idP]
        if(i%10000==0):
            perc = (i*100)/l
            perc = str(perc)
            perc = perc[0:5]
            tm = time.asctime()
            tm = tm.split(' ')
            tm = tm[3]
            print('['+tm+'] Processed '+str(perc)+' - '+str(i)+' papers - ') 
        i+=1
    end()
    return authJson1

### Get the fuzzy-searched dataset
#
#fuzzyP = fuzzy_search(corpus_path, journal_list)
##len(fp) = 15.213
#
### Get papers from file and create the dataset
#
#papers = getP(fuzzy_path)
#PTIds = getPaperSet(papers)
#start()
#print("Starting file creation...")
#pTestingJSON, authoring, citations = getPapersTestingJSON(papers, PTIds)
#papersTestingForSearchFile(destination_path, pTestingJSON, authoring, citations)
#end()
##>> OUT:
#
##>>15213 papers loaded, 0 discarded
##>>Total inC = 375540 - inInP = 87569
##>>Total outC = 310357 - outInP = 87569
# 
### Create and write the authors' dataset
#
#get A, authors of at least one paper in P
#authJSON = getAuthJson(papers)
#A = authorsJSONObj(papers, authJSON)
### once A is ready you can write it with
#authorsForSearchFile(path, A)
#auth_file = r"C:/**/a_v0518f.txt"
#authorsForSearchFile(auth_file, A)
##> len(A) = 19.464