import requests, re, os
from bs4 import BeautifulSoup
from datetime import datetime


def set_constants():
    spliter = '\n=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*\n'

    return re.compile(r'\s\s+'), spliter


def get_total_document_number(soup):
    num = soup.select('span.number').pop().text.split('/')[1].replace(',', '')[:-1]

    return int(num)


#===================질문링크===================#
def get_links(soup, links):
    for a_tag in soup.select('ul.basic1 a._searchListTitleAnchor'):
        links.append(a_tag.attrs['href'])

    return links


def get_number_of_answer(soup, answer_num):
    for span_tag in soup.select('ul.basic1 dd.txt_block span.hit'):
        answer_num.append(int(span_tag.text.split(' ')[1]))

    return answer_num


def get_outer_info():
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    num = get_total_document_number(soup)
    links = []

    last_page = num // 10
    if num % 10 != 0: last_page += 1
    current_page = 1

    while current_page <= last_page:
        links.extend(get_links(soup, []))

        current_page += 1
        html = requests.get(url+'&page='+str(current_page)).text
        soup = BeautifulSoup(html, 'html.parser')

    return links, num


#===================질문내용===================#
def get_qna():
    questions = []
    answers = []
    userinfos = []
    questioned_dates = []

    cnt = -1
    for idx in range(0, len(links)):
        content = requests.get(links[idx]).text
        soup = BeautifulSoup(content, 'html.parser')

        if len(soup.select('div._questionContentsArea')) <= 0: # 제대로 안들어가지면
            cnt += 1
            continue

        question = soup.select('#content .c-heading__content')
        if len(question) == 0:
            question = soup.select('#content .c-heading__title-inner')

        questions.append(re.sub(pattern, '', question.pop().text))
        questioned_dates.append(soup.select('div.question-content span.c-userinfo__date').pop().text.split('일')[1])

        answer = soup.select('._answerList se-main-container')

        if len(answer) == 0:
            answer = soup.select('._answerList .c-heading-answer__content-user')

        answer_list = []
        for a in answer:
            clean_text = re.sub(pattern, '', a.text).replace('\u200b', ' ').replace('\xa0', ' ')
            if not clean_text in answer_list:
                answer_list.append(clean_text)

        answers.append(answer_list)

        user_list = []
        user = soup.select('._answer .c-heading-answer__title')
        for usr in user:
            info = re.sub(pattern, '', usr.text)

            if '보험' in info:
                usrType = '보험'
            elif '한의' in info or '한방' in info:
                usrType = '한의학'
            elif '의' in info or '과' in info or '클리닉' in info:
                usrType = '양의햑'
            else:
                usrType = '기타'

            user_list.append(usrType)

        userinfos.append(user_list)

    return questions, questioned_dates, answers, userinfos, cnt


def data_in():
    query = input('검색어 : ')
    query.replace(' ', '+')
    _from = input('from (YYYY.MM.DD.) : ')
    _to = input('to (YYYY.MM.DD.) : ')
    url = 'https://kin.naver.com/search/list.nhn?sort=date' + '&query='+query + '&period='+_from+'%7C'+_to+'&section=kin'

    return query, _from+'.%7C'+_to, url


def create_file_one():
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    start_date = period.split('.%7C')[0][:-1].replace('.', '')
    end_date = period.split('.%7C')[1][:-1].replace('.', '')
    DIR_NAME = '[' + current_time + ']' + start_date + '-' + end_date
    FILE_NAME = start_date+'-'+end_date+'.txt'

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
            #print('len of questions : '+str(len(questions)))
            file.write('Q.'+str(q_idx+6686)+') '+dates[q_idx]+'\n'+questions[q_idx]+'\n\n')

            for a_idx in range(0, len(answers[q_idx])):
                #print('q_idx, a_idx, len of userInfo[q_idx] : ' +str(q_idx)+'///'+str(a_idx)+'//////'+str(len(userInfos[q_idx])))
                file.write('A.'+str(q_idx+6686)+'-'+str(a_idx+1)+') '+userInfos[q_idx][a_idx]+'\n'+answers[q_idx][a_idx]+'\n\n')

            file.write(spliter)

        read_me.write('skipped document : '+str(skipped))

    read_me.close()
    file.close()


if __name__ == "__main__":
    global links, titles, total_num, questions, answers, url, pattern, \
        html, soup, query, dates, userInfos, answer_num, spliter, skipped

    pattern, spliter = set_constants()
    query, period, url = data_in()
    links, total_num = get_outer_info()
    questions, dates, answers, userInfos, skipped = get_qna()
    create_file_one()

