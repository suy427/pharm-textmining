import datetime

file = open('result.txt', 'r')
lines = file.readlines()

data = []

for idx in range(0, len(lines), 5):
    date = datetime.datetime.strptime(lines[idx+1][:-1], '%Y-%m-%d').date()
    answer_num = lines[idx+2][:-1]
    doctor_num = lines[idx+3].count('d')
    oriental_num = lines[idx+3].count('o')
    else_num = lines[idx+3].count('e')
    data.append([date,answer_num,[doctor_num,oriental_num,else_num]])


data = sorted(data, key=lambda x: x[0])

for idx in range(0, len(data)):
    data[idx][0] = data[idx][0].strftime('%Y-%m-%d')


for da in data:
    print(da)

print('===================================')

result = []
for year in range(2003, 2020):
    for month in range(1, 13):
        a_num = 0
        q_num = 0
        d_num = 0
        o_num = 0
        e_num = 0
        for idx in range(0, len(data)):
            date = data[idx][0].split('-')
            if date[0] == str(year) and int(date[1]) == month:
                a_num += int(data[idx][1])
                q_num += int(data[idx][2])
                d_num += int(data[idx][3][0])
                o_num += int(data[idx][3][1])
                e_num += int(data[idx][3][2])

        result.append([a_num, [d_num, o_num, e_num]])


file2 = open('final.txt', 'w')

cnt = 0
for year in range(2003, 2020):
    for month in range(1, 13):
        file2.write(str(year)+'/'+str(month)+'\n')
        file2.write(str(result[cnt])+'\n\n')
        cnt += 1
