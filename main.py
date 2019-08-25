import requests, re, os
from bs4 import BeautifulSoup
from datetime import datetime
import time


################################################################################
#
# 출력시에 도큐먼트별로 구분하기 위한 구분자(spliter), 정규표현식으로 Tokenizing할 때 쓸 패턴(pattern)
#
################################################################################
def set_constants():
    spliter = '\n=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*\n'

    return re.compile(r'\s\s+'), spliter


################################################################################
#
# 지식인에서 키워드 검색 후 나오는 게시글 리스트 화면에 뜨는 전체 문서수를 크롤링
#
################################################################################
def get_total_document_number(soup):
    num = soup.select('span.number').pop().text.split('/')[1].replace(',', '')[:-1]
    #print('######################'+num)

    return int(num)


################################################################################
#
# 질문 리스트들의 제목(하이퍼링크)를 통해 각 게시물들의 링크를 크롤링함
#
################################################################################
#===================질문링크===================#
def get_links(soup, links):
    for a_tag in soup.select('ul.basic1 a._searchListTitleAnchor'):
        links.append(a_tag.attrs['href'])

    return links


def get_title(soup, titles):
    for a_tag in soup.select('ul.basic1 a._searchListTitleAnchor'):
        titles.append(a_tag.text)

    return titles

################################################################################
#
# 각 질문별 답변갯수를 크롤링함
# 여기까지는 검색결과 페이지를 크롤링해서 얻는 정보들임
#
################################################################################
def get_number_of_answer(soup):
    tmp = 0
    for span_tag in soup.select('ul.basic1 dd.txt_block span.hit'):
        #answer_num.append(int(span_tag.text.split(' ')[1]))
        tmp += int(span_tag.text.split(' ')[1])

    return tmp


################################################################################
#
# 검색결과 페이지에 얻는 정보를 모두 가져옴
# 각 게시글들의 링크, 전체 문서수
#
################################################################################
def get_outer_info():
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    num = get_total_document_number(soup)
    links = []
    titles = []

    # 전체 문서수를 가지고 마지막 페이지를 알아냄. URL에 이 정보를 넣어서 크롤링해야함.
    last_page = num // 10
    if num % 10 != 0: last_page += 1
    current_page = 1

    while current_page <= last_page:
        links.extend(get_links(soup, []))
        titles.extend(get_title(soup, []))

        current_page += 1
        html = requests.get(url+'&page='+str(current_page)).text # 이부분에서 &page=이후에 페이지 정보가 들어감
        soup = BeautifulSoup(html, 'html.parser')

    return links, num, titles


################################################################################
#
# 바쁘고 귀찮아서 제대로 모듈화를 못했는데 주영아 부탁한다...ㅎㅠㅠ
# 검색결과 페이지에서 각 게시글들의 링크를 받아왔으므로 이제 각 링크에 들어가서
# 해당 게시글들의 내용을 크롤링함.
#
################################################################################
def get_qna():
    questions = []
    answers = []
    userinfos = []
    questioned_dates = []
    usr_type = [0, 0, 0, 0]

    # 각각의 게시물들의 크롤링은 검색결과 페이지에서 얻어온 링크들에 직접 리퀘스트를 날려서 받은 html을 대상으로 하는데
    # 성인인증이 필요한 게시글의 경우 정상적으로 얻을 수 있는 질문과 답변내용이 포함된 html이 아닌 다른 html을 받게됨.
    # 그런 경우에는 continue를 통해서 과감하게 해당 게시글은 skip하고 cnt를 올려서 그런 게시글들이 얼마나 있는지 계수함.
    # 추후 이 cnt가 너무 많아서 표본 데이터를 만드는데 영향을 크게 끼친다면 selenium을 통해서 직접 로그인한 후에 크롤링 해야할듯.
    cnt = -1
    for idx in range(0, len(links)):
        if '태아' in titles[idx]:
            continue

        content = requests.get(links[idx]).text
        soup = BeautifulSoup(content, 'html.parser')

        if len(soup.select('div._questionContentsArea')) <= 0: # 해당 태그에 질문내용이 있는데 이 태그를 가져오지 못했다는건
            cnt += 1                                           # 질문이 없는 페이지(잘못된 페이지)라는거임
            continue                                           # 따라서 cnt 올리고 continue해서 skip함


        ################################################################################
        #
        # 밑에부터는 질문, 답변내용을 크롤링하는 부분인데
        # 확인해보면 공통적으로 먼저 '질문'태그를 크롤링한 다음 제대로 크롤링이 안되면
        # 어떤 다른 태그를 크롤링하여 내용을 추출한것을 확인할 수 있다.
        # 이건 전에 말한것처럼 작성자들이 지식인 게시글 이용정책을 무시하고 글을 올렸기 때문인데
        # question의 경우 'c-heading__content'가 질문의 내용이 있는 태그라 여기를 크롤링하고
        # 이게 없으면 작성자가 제목을 적는란에 내용까지 모두 적었다는 이야기다.
        # 그래서 'c-heading__title-inner'로 제목란을 크롤링한다
        #
        ################################################################################
        question = soup.select('#content .c-heading__content')
        if len(question) == 0:
            question = soup.select('#content .c-heading__title-inner')

        clean_question = re.sub(pattern, '', question.pop().text)
        #print(clean_question)
        if '태아' in clean_question:
            #print('ooooooooooo')
            continue
        else:
            questions.append(clean_question)

        # 원래는 질문 작성일을 검색결과페이지(바깥페이지)에서 가져왔었는데 내용 페이지에도 이 내용이 있어서
        # 여기서 한꺼번에 크롤링하기로 했다.
        # 그런데 문제점이 검색결과 페이지에서 보이는 작성날짜와 실제 질문글 내용페이지 안에서 확인할 수 있는 작성날짜가 다른경우가 있다는 것이다.
        # 이경우는 아직까지 그 원인을 모르겠는데 아마도 내용페이지에서 보이는 페이지가 실제 작성일자이고 검색결과 페이지에서 보이는 날짜가
        # 수정된날짜 인듯하다.
        questioned_dates.append(soup.select('div.question-content span.c-userinfo__date').pop().text.split('일')[1])
        #print(questions)
        ################################################################################
        #
        # 답변의 경우도 질문과 마찬가지로 작성자가 정책을 지키지 않고 엉뚱한 form에 답변을 작성하거나
        # 홍보 등과 같은 이유로 질문 내용에 html 태그를 사용해 글을 작성한 경우.. 등등 다양한 변수들이 있었다
        # (질문 크롤링하는것보다 더 어려웠음...)
        # 해서 처음에는 '_answerList se-main-container'를 크롤링하고 없을경우
        # 'c-heading-answer__content-user' 를 크롤링한다.
        # 참고로 question과 answer모두 처음부터 두번째 태그를 크롤링하면 안되는건가 생각할 수 있겠지만
        # 안된다...ㅜ
        #
        ################################################################################
        answer = soup.select('._answerList se-main-container')
        if len(answer) == 0:
            answer = soup.select('._answerList .c-heading-answer__content-user')

        ################################################################################
        #
        # answer의 경우 question과 다르게 복수개이므로 처음에 모든 answer들을 크롤링하여 List로 만들고
        # 반복문 안에서 정제한 후에 해당 question에 대한 답변List로 색인한다.
        #
        ################################################################################
        answer_list = []
        exept = []
        for idx in range(0, len(answer)):
            clean_answer = re.sub(pattern, '', answer[idx].text).replace('\u200b', ' ').replace('\xa0', ' ')
            if clean_answer in answer_list:
                continue
            else:
                if '태아' in clean_answer:
                    exept.append(idx)
                else:
                    answer_list.append(clean_answer)

        answers.append(answer_list)
        #print('@@@@@@@@@@@@@'+str(exept))
        ################################################################################
        #
        # 답변자 정보같은 경우 네이버에 자신의 정보를 등록한 이용자의 경우에는 따로 '네임카드'가 붙어서
        # 네임카드의 내용을 크롤링할 수 있다. 그러나 그렇지 않은경우에는 답변 제목이나 내용을 봐야하는데
        # 내용에 '병원' 등의 특정 단어가 들어간다고 해서 그 답변의 작성자가 의사라고 단정할 수는 없기 때문에
        # 네임카드를 크롤링하여 답변자 정보를 알아내는 것이 지금으로는 최선인듯하다.
        # 아래의 코드는 네임카드를 크롤링하여 그 내용중에 '보험', '한의', '한방' 등의 특정 단어의 여부로
        # 사용자 정보를 분류하는 내용이다. 반드시 '한의', '한방'을 체크하는 elif가 '의', '과'등을 체크하는 elif
        # 보다 먼저 있어야한다. 그렇지 않으면 '의'가 들어있다고 해서 '한의사'와 같은 정보도 양의학으로 분류할 수 있다.
        #
        ################################################################################
        user_list = []
        user = soup.select('._answer .c-heading-answer__title')
        # how = 0
        # tw = 1
        # for ttt in user:
        #     print(str(tw)+ttt.text)
        #     tw += 1
        # print('\n\n$$$$$$$$$$$$$$$$$$$\n\n')

        for idx in range(0, len(user)):
            if idx in exept:
                continue
            info = re.sub(pattern, '', user[idx].text)

            if '삭제' in info:
                continue
            elif '작성중' in info:
                continue

            if '보험' in info:
                usrType = '보험'
                usr_type[0] += 1
                # how += 1
            elif '한의' in info or '한방' in info:
                usrType = '한의학'
                usr_type[1] += 1
                # how += 1
            elif '의' in info or '과' in info or '클리닉' in info:
                usrType = '양의햑'
                usr_type[2] += 1
                # how += 1
            else:
                usrType = '기타'
                usr_type[3] += 1
                # how += 1

            user_list.append(usrType)

        #print(usr_type, end=', '+str(how)+'\n')###################TEST#####################
        userinfos.append(user_list)

    return questions, questioned_dates, answers, userinfos, cnt, usr_type


def data_in():
    query = input('검색어 : ')
    query.replace(' ', '+')
    _from = input('from (YYYY.MM.DD.) : ')
    _to = input('to (YYYY.MM.DD.) : ')
    url = 'https://kin.naver.com/search/list.nhn?sort=date' + '&query='+query + '&period='+_from+'%7C'+_to+'&section=kin'

    return query, _from+'.%7C'+_to, url


def create_file():
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    start_date = period.split('.%7C')[0][:-1].replace('.', '')
    end_date = period.split('.%7C')[1][:-1].replace('.', '')
    DIR_NAME = '[' + current_time + ']' + start_date + '-' + end_date
    FILE_NAME = start_date+'-'+end_date+'.txt'
    offset = 5148

    try:
        if not os.path.isdir(DIR_NAME):
            os.makedirs(os.path.join(DIR_NAME))

    except Exception as e:
        print('fail to make root directory')
        raise

    if not os.path.isfile(DIR_NAME+FILE_NAME): #없으면
        file = open(DIR_NAME+'/'+FILE_NAME, 'w')
        read_me = open(DIR_NAME + '/' + 'READ ME.txt', 'w')

        for q_idx in range(0, len(questions)):
            file.write('Q.'+str(q_idx+offset)+') '+dates[q_idx]+'\n'+questions[q_idx]+'\n\n')

            for a_idx in range(0, len(answers[q_idx])):
                file.write('A.'+str(q_idx+offset)+'-'+str(a_idx+1)+') '+userInfos[q_idx][a_idx]+'\n'+answers[q_idx][a_idx]+'\n\n')

            file.write(spliter)

        read_me.write('skipped document : '+str(skipped))

    read_me.close()
    file.close()


if __name__ == "__main__":
    global links, total_num, questions, answers, url, pattern, titles,\
        html, soup, query, dates, userInfos, answer_num, spliter, skipped, user_info_cnt

    start = time.time()

    pattern, spliter = set_constants()
    query, period, url = data_in()
    links, total_num, titles = get_outer_info()
    questions, dates, answers, userInfos, skipped, user_info_cnt = get_qna()
    create_file()
    print(period.replace('.%7C', '-'))
    print('questions : '+str(len(questions)))
    answer_num = 0
    for a in answers:
        #print('answer List ('+str(len(a))+')'+': ' + str(a))###################TEST#####################
        answer_num += len(a)
    print('answers : '+str(answer_num))
    print('[ensurance, oriental, medical, etc] : '+str(user_info_cnt))
    print('\n==================\n')
    print('spent time : '+str(round(time.time()-start, 2)))
    print('sum : '+str(user_info_cnt[0]+user_info_cnt[1]+user_info_cnt[2]+user_info_cnt[3]))
    os.system('say "다 끝났어"')


#===================================================================================================

# 2016.09.01.-2016.12.31.
# questions : 1154
# answers : 2617
# [ensurance, oriental, medical, etc] : [66, 62, 1088, 1401] 2016.11.09. 특수케이스!!!! @@@@@Q.550@@@@@

# 2017.01.01.-2017.05.01.
# questions : 1045
# answers : 2404
# [ensurance, oriental, medical, etc] : [23, 75, 780, 1526]

# 2017.05.02.-2017.11.30.
# questions : 1037
# answers : 2003
# [ensurance, oriental, medical, etc] : [44, 99, 434, 1426]

# 2017.12.01.-2017.12.31.
# questions : 94
# answers : 185
# [ensurance, oriental, medical, etc] : [2, 2, 29, 152]

# 2018.01.01.-2018.07.31.
# questions : 718
# answers : 1307
# [ensurance, oriental, medical, etc] : [50, 68, 242, 947]

# 2018.08.01.-2018.12.31.
# questions : 711
# answers : 1765
# [ensurance, oriental, medical, etc] : [63, 91, 502, 1109]

# 2019.01.01.-2019.08.14.
# questions : 931
# answers : 2052
# [ensurance, oriental, medical, etc] : [34, 194, 348, 1476]