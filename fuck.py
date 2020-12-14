import requests
import json
import time
import random
import re
import hashlib

answer_dictionary = {}

hit_count = 0

def ReadAnswerFromFile():
    global answer_dictionary
    answer_file = open('answer.txt', 'r')
    answer_dictionary = json.loads(answer_file.read())
    print("已读取", len(answer_dictionary.items()), "个答案！")
    answer_file.close()



def SaveAnswerToFile():
    global answer_dictionary
    answer_file = open('answer.txt', 'w')
    answer_file.write(json.dumps(answer_dictionary))
    print("已保存", len(answer_dictionary.items()), "个答案！")
    answer_file.close()



def BuildHeader(token):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-GB,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Host': 'ssxx.univs.cn',
        'Referer': 'http://ssxx.univs.cn/client/exam/5f71e934bcdbf3a8c3ba5061/1/1/5f71e934bcdbf3a8c3ba51d5',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
        'Authorization': 'Bearer ' + token,
    }

    return headers



def PrintQuizObject(quiz_object):
    print("问题ID列表：")
    for i in range(0, 20):
        print("问题", i, "：", quiz_object["question_ids"][i])



def StartQuiz(header):
    global hit_count
    hit_count = 0

    print("尝试开始考试……")

    url = "http://ssxx.univs.cn/cgi-bin/race/beginning/?activity_id=5f71e934bcdbf3a8c3ba5061&mode_id=5f71e934bcdbf3a8c3ba51d5&way=1"

    response = requests.request("GET", url, headers = header)

    quiz_object = json.loads(response.text)

    if quiz_object["code"] != 0:
        print("开始考试失败，状态码：", quiz_object["code"], "错误原因：", quiz_object["message"])
        quit(0)

    print("开始考试成功，本次考试信息如下：")
    print("race_code", quiz_object["race_code"])

    return quiz_object["question_ids"], quiz_object["race_code"]



def GetTitleMd5(title):
    print("原title：", title)
    title = re.sub(r"<(\w+)[^>]+?(?:display: {0,}none;).*?>.*?<\/\1>", "", title)
    title = re.sub("<.*?>", "", title)
    print("title特征值：", title)
    result = hashlib.md5(title.encode(encoding='UTF-8')).hexdigest()
    print("title哈希码：", result)
    return result



def GetQuestionDetail(question_id, header):
    url = "http://ssxx.univs.cn/cgi-bin/race/question/?activity_id=5f71e934bcdbf3a8c3ba5061&question_id=" + question_id + "&mode_id=5f71e934bcdbf3a8c3ba51d5&way=1"

    response = requests.request("GET", url, headers = header)

    question_detail_object = json.loads(response.text)
    if question_detail_object["code"] != 0:
        print("获取题目信息失败。问题ID：", question_id, "错误代码：", question_detail_object["code"], "错误信息：", question_detail_object["message"])
        quit(-1)
        
    else:
        print("获取题目信息成功。当前问题：")
        print(question_detail_object["data"]["title"])
    
    question = {}
    question["id"] = question_detail_object["data"]["id"]
    question["title"] = GetTitleMd5(question_detail_object["data"]["title"])
    question["answer_list"] = []
    for i in question_detail_object["data"]["options"]:
        question["answer_list"].append((i["id"], GetTitleMd5(i["title"])))
    
    return question

def BuildAnswerObject(question):
    global answer_dictionary
    global hit_count

    print("正在尝试寻找答案……")

    answer_object = {
        "activity_id": "5f71e934bcdbf3a8c3ba5061",
        "question_id": question["id"],
        "mode_id": "5f71e934bcdbf3a8c3ba51d5",
        "way": "1"
    }

    if answer_dictionary.__contains__(question["title"]):
        hit_count += 1
        print("答案库中存在该题答案")
        answer_object["answer"] = []
        for i in question["answer_list"]:
            if i[1] in answer_dictionary[question["title"]]:
                answer_object["answer"].append(i[0])
    else:
        print("答案库中不存在该题答案，蒙一个A选项吧")
        answer_object["answer"] = [question["answer_list"][0][0]]

    return answer_object, question



def SubmitAnswer(answer_object, header):
    global answer_dictionary

    url = "http://ssxx.univs.cn/cgi-bin/race/answer/"

    header["Content-Type"] = "application/json"

    response = requests.request("POST", url, headers = header, data = json.dumps(answer_object[0]))

    result_object = json.loads(response.text)
    if not result_object["data"]["correct"] and answer_dictionary.__contains__(answer_object[1]["title"]):
        print("答案库中已有答案但不正确！")
    elif result_object["data"]["correct"] and answer_dictionary.__contains__(answer_object[1]["title"]):
        return True
    elif result_object["data"]["correct"] and not answer_dictionary.__contains__(answer_object[1]["title"]):
        print("运气不错，居然蒙对了，保存答案")
    elif not result_object["data"]["correct"] and not answer_dictionary.__contains__(answer_object[1]["title"]):
        print("答案错误，更新答案")

    if not answer_dictionary.__contains__(answer_object[1]["title"]):
        answer_dictionary[answer_object[1]["title"]] = []

    for i in result_object["data"]["correct_ids"]:
        print("服务器返回的正确答案：", i)
        for j in answer_object[1]["answer_list"]:
            if i == j[0]:
                print("已在问题列表中找到该答案，元组为", j)
                answer_dictionary[answer_object[1]["title"]].append(j[1])
                break

    return result_object["data"]["correct"]



def FinishQuiz(race_code):
    url = "http://ssxx.univs.cn/cgi-bin/race/finish/"

    header["Content-Type"] = "application/json"
    payload = "{\"race_code\":\"" + race_code + "\"}"

    result = json.loads(requests.request("POST", url, headers = header, data = payload).text)
    while result["code"] != 0:
        print("完成考试时出错，错误代码：", result)
        time.sleep(0.5)
        result = json.loads(requests.request("POST", url, headers = header, data = payload).text)

    print("回答完毕，本次得分：", result["data"]["owner"]["correct_amount"], "答案库命中数：", hit_count)



ReadAnswerFromFile()
print("请输入token（登录后按F12，转到Console页面，输入localStorage.token后回车，输出的结果中 不 带 引 号 的 部 分 复制下来并输入即可）：")
token = input()
header = BuildHeader(token)
while True:
    question_list, race_code = StartQuiz(header)
    for i in range(0, 20):
        if SubmitAnswer(BuildAnswerObject(GetQuestionDetail(question_list[i], header)), header):
            print("第", i, "题回答正确！")
            time.sleep(float(random.randint(500, 1500)) / 1000)
        else:
            print("第", i, "题回答错误，答案已更新！")
            time.sleep(float(random.randrange(1500, 3000)) / 1000)
            SaveAnswerToFile()
    FinishQuiz(race_code)
    # SaveAnswerToFile()
    time.sleep(float(random.randrange(1500, 3000)) / 1000)