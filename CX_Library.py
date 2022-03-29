import queue
import re
import threading

import requests
import base64
import time
from datetime import date, timedelta


class Library:
    def __init__(self, phone, password):
        self.today = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.acc = phone
        self.pwd = password
        self.deptIdEnc = ""
        self.deptId = ""
        self.status = {
            '0': '待履约',
            '1': '学习中',
            '2': '已履约',
            '3': '暂离中',
            '5': '被监督中',
            '7': '已取消',
        }
        self.room = None
        self.room_id_capacity = {}
        self.db = {
            'sb': 0,
            'nb': 0
        }
        # with open('./info.json', 'r', encoding='utf8') as fp:
        #     all_seat = json.load(fp)
        self.all_seat = []
        self.room_id_name = {}
        self.emptyInfo = []
        self.session = requests.session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 '
                          '(KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
        }
        self.login()

    @classmethod
    def t_time(cls, timestamp, t_type):
        t_format = "%Y-%m-%d %H:%M:%S" if t_type == 1 else "%H:%M:%S"
        return time.strftime(t_format, time.localtime(int(str(timestamp)[0:10])))

    def login(self):
        c_url = 'https://passport2.chaoxing.com/mlogin?' \
                'loginType=1&' \
                'newversion=true&fid=&' \
                'refer=http%3A%2F%2Foffice.chaoxing.com%2Ffront%2Fthird%2Fapps%2Fseat%2Findex'
        self.session.get(c_url).cookies.get_dict()
        data = {
            'fid': '-1',
            'uname': self.acc,
            'password': base64.b64encode(self.pwd.encode()).decode(),
            'refer': 'http%3A%2F%2Foffice.chaoxing.com%2Ffront%2Fthird%2Fapps%2Fseat%2Findex',
            't': 'true'
        }
        self.session.post('https://passport2.chaoxing.com/fanyalogin', data=data)
        s_url = 'https://office.chaoxing.com/front/third/apps/seat/index'
        self.session.get(s_url)

    # 签到
    def sign(self):
        info = self.get_my_seat_id()
        data_i = []
        for index in info:
            if index['status'] == 1:
                location = index['firstLevelName'] + index['secondLevelName'] + index['thirdLevelName'] + index[
                    'seatNum']
                return "{}:已经签过到了，快学习吧~".format(location)
            if index['status'] == 0 or index['status'] == 3 or index['status'] == 5:
                data_i.append(index)
                continue
        location = None
        seatid = None
        inital = 9999999999999
        if data_i:
            if len(data_i) >= 2:
                for index in data_i:
                    if int(index['startTime']) < inital:
                        inital = index['startTime']
                        seatid = index['id']
                        location = index['firstLevelName'] + index['secondLevelName'] + index['thirdLevelName'] + index[
                            'seatNum']
            else:
                seatid = data_i[-1]['id']
                location = data_i[-1]['firstLevelName'] + data_i[-1]['secondLevelName'] + \
                           data_i[-1]['thirdLevelName'] + data_i[-1]['seatNum']
            response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/sign?id={}'.format(seatid))
            if response.json()['success']:
                print(self.acc, '签到', '成功', location)
                return "{}：签到成功".format(location)
            return "{}：{}".format(location, response.json()['msg'])
        return "没有座位可以签到"

    # 暂离
    def leave(self):
        info = self.get_my_seat_id()
        for index in info:
            if index['status'] == 1:
                location = index['firstLevelName'] + index['secondLevelName'] + index['thirdLevelName'] + index[
                    'seatNum']
                response = self.session.get(
                    url='https://office.chaoxing.com/data/apps/seat/leave?id={}'.format(index['id']))
                if response.json()['success']:
                    return "{}：暂离成功".format(location)
                return "{}：{}".format(location, response.json()['msg'])
        return "当前没有座位可暂离"

    # 退座
    def signback(self):
        info = self.get_my_seat_id()
        for index in info:
            if index['status'] == 1 or index['status'] == 3 or index['status'] == 5:
                location = index['firstLevelName'] + index['secondLevelName'] + index['thirdLevelName'] + index[
                    'seatNum']
                response = self.session.get(
                    url='https://office.chaoxing.com/data/apps/seat/signback?id={}'.format(index['id']))
                if response.json()['success']:
                    return "{}：座位已退出".format(location)
                return "{}：{}".format(location, response.json()['msg'])
        return "当前没有座位可退"

    # 取消
    def cancel(self):
        info = self.get_my_seat_id()
        for index in info:
            if index['status'] == 0 or index['status'] == 3 or index['status'] == 5:
                location = index['firstLevelName'] + index['secondLevelName'] + index['thirdLevelName'] + index[
                    'seatNum']
                response = self.session.get(
                    url='https://office.chaoxing.com/data/apps/seat/cancel?id={}'.format(index['id']))
                if response.json()['success']:
                    return "{}：座位已取消".format(location)
                return "{}：{}".format(location, response.json()['msg'])
        return "当前没有座位可取消"

    # 获取到最近一次预约的座位ID
    def get_my_seat_id(self):
        response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/reservelist?'
                                        'indexId=0&'
                                        'pageSize=100&'
                                        'type=-1').json()['data']['reserveList']
        result = []
        for index in response:
            if index['type'] == -1:
                if index['today'] == self.today or index['today'] == self.tomorrow:
                    result.append(index)
        return result

    # 预约座位 需要自己修改
    def submit(self, seatNum, day):
        # 注意 老版本的系统需要将url中的seat改为seatengine且不需要第一步获取list。有可能需要提供seatId的值
        # 获取token
        response = self.session.get(url='https://office.chaoxing.com/front/apps/seat/list?'
                                        f'deptIdEnc={self.deptIdEnc}')
        pageToken = re.compile(r"&pageToken=' \+ '(.*)' \+ '&").findall(response.text)[0]
        response = self.session.get(url='https://office.chaoxing.com/front/apps/seat/select?'
                                        'id=3752&'  # 房间id roomId 可以从self.room_id_name获取 请自行发挥
                                        f'day={day}&'  # 预约时间 上下需保持一致
                                        'backLevel=2&'  # 必须的参数2
                                        f'pageToken={pageToken}')
        token = re.compile("token: '(.*)'").findall(response.text)[0]
        response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/submit?'
                                        'roomId=3752&'  # 房间id roomId 上下需保持一致
                                        'startTime=9%3A30&'  # 开始时间%3A代表: 自行替换9（小时）和后面00（分钟） 必须
                                        'endTime=22%3A00&'  # 结束时间 规则同上
                                        f'day={day}&'  # 预约时间 上下需保持一致
                                        f'seatNum={seatNum}&'  # 座位数字 与桌上贴纸一致
                                        f'token={token}')
        seat_result = response.json()
        print(seat_result)

        if seat_result["success"]:
            info = seat_result["data"]["seatReserve"]
            seatInfo = info["firstLevelName"] + info["secondLevelName"] + info["thirdLevelName"] + info["seatNum"]
            startTime = self.t_time(info["startTime"], 1)
            endTime = self.t_time(info["endTime"], 2)
            lastTime = info["duration"]
            print("预约成功! {}\n{}至{}共{}小时".format(seatInfo, startTime, endTime, lastTime))

    # 获取图书馆所有的房间和座位
    def get_all_room_and_seat(self):
        # 注意 老版本的系统需要将url中的seat改为seatengine，且可能需要附带seatId的值
        response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/room/list?'
                                        f'deptIdEnc={self.deptIdEnc}')
        self.room = response.json()['data']['seatRoomList']
        # deptId = self.room[0]['deptId']

        for index in self.room:
            self.room_id_capacity[index['id']] = index['capacity']
            self.db[index['id']] = 0
            self.room_id_name[index['id']] = index['firstLevelName'] + index['secondLevelName'] + index[
                'thirdLevelName']
            response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/seatgrid/roomid?'
                                            'roomId={}'.format(index['id']))
            self.all_seat += response.json()['data']['seatDatas']
        print("ALL获取完成")

    # 获取学习人数分布 多线程 2000座约10s
    # 注意 老版本的系统接口可能不能获取到
    def get_study_info(self):
        q = queue.Queue()
        for item in self.all_seat:
            # print(item["roomId"])
            if item["roomId"] == 3752:
                q.put(item)
        ths = []
        for idx in range(0, 233):
            ths.append(
                threading.Thread(target=self.get_seat_info, args=(q,))
            )
        for th in ths:
            th.start()
        for th in ths:
            th.join()

        # print('有人\t', '没人\t', '总共\t', '地点\t')
        # for index in self.room:
        #     print(self.db[index['id']], ' ', '\t', self.room_id_capacity[index['id']] - self.db[index['id']], '\t',
        #           self.room_id_capacity[index['id']], '\t', self.room_id_name[index['id']])
        # print(self.db['sb'], '\t', self.db['nb'], '\t', len(self.all_seat))

        # 筛选座位 修改145可以看所有楼层的145座位信息 自行发挥
        # for index in self.all_seat:
        #     if index['seatNum'] == '145':
        #         print(index['seatNum'], index['id'], index['roomId'], self.room_id_name[index['roomId']])
        #     continue

    # 获取座位详细信息 配合get_study_info
    def get_seat_info(self, q: queue.Queue):
        data = ""
        while True:
            seat = q.get()
            # 注意 老版本的系统不支持此接口
            response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/reserve/info?'
                                            'id={0}&seatNum={1}'.format(seat['roomId'], seat['seatNum'])).json()
            # print(response)
            try:
                data = response["data"]
                # r = data["seatReserve"]
                self.db[seat['roomId']] += 1
                self.db['sb'] += 1
            except:
                self.db['nb'] += 1
                if int(seat['seatNum']) % 2 == 1:
                    usedTime = self.get_used_times(seat['roomId'], seat['seatNum'], self.today)
                    self.emptyInfo.append(
                        str(self.room_id_name[seat['roomId']] + seat['seatNum'] + '目前无人使用\n' + usedTime))
            if q.empty():
                break

    # 查询签到位置范围
    def get_sign_addr(self):
        response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/address?'
                                        f'deptId={self.deptId}')
        for index in response.json()['data']['addressArr']:
            print(index['location'], index['offset'])

    # 获取座位占用时间段
    def get_used_times(self, roomId, seatNum, day):
        response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/getusedtimes?'
                                        f'roomId={roomId}&seatNum={seatNum}&day={day}')
        result = "占用时段:"
        res = response.json()
        if res["success"]:
            data = res["data"]
            if len(data) > 0:
                for t in data:
                    start = self.t_time(t[0], 2)
                    end = self.t_time(t[1], 2)
                    result += str(start + '-' + end + " ")
            else:
                result += "今日剩余时段都空闲"
            return result


if __name__ == '__main__':
    lib = Library("", "")
