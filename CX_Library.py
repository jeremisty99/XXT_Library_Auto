import queue
import re
import threading
from lxml import etree
import check
import requests
import base64
import time
from datetime import date, timedelta

from Crypto.Cipher import AES


class Library:
    def __init__(self, phone, password, version):
        self.version = version  # 当前系统是否为旧版 0为旧版
        self.today = (date.today()).strftime("%Y-%m-%d")
        self.tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.acc = self.encrypt(phone)
        self.pwd = self.encrypt(password)
        self.seatId = None  # 旧版系统参数
        self.deptIdEnc = None
        self.deptId = None
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
        self.room_id_name = {}
        self.all_seat = []
        self.emptyInfo = []
        self.session = requests.session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 '
                          '(KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
        }
        self.login()

    @classmethod
    def encrypt(cls, input):
        key = "u2oh6Vu^HWe4_AES"
        aeskey = key.encode('utf-8')
        iv = key.encode('utf-8')

        # 使用 CBC 模式和 PKCS7 填充
        CBCOptions = AES.new(aeskey, AES.MODE_CBC, iv=iv)
        pad = lambda s: s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)
        secretData = pad(input).encode('utf-8')

        # 加密并返回 Base64 编码后的密文
        encrypted = CBCOptions.encrypt(secretData)
        return base64.b64encode(encrypted).decode('utf-8')

    @classmethod
    def t_time(cls, timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(str(timestamp)[0:10])))

    @classmethod
    def get_date(cls):
        return time.strftime('%a %b %d %Y %I:%M:%S GMT+0800 ', time.localtime(time.time())) + '(中国标准时间)'

    @classmethod
    def t_second(cls, timestamp):
        if timestamp:
            m, s = divmod(int(str(timestamp)[0:-3]), 60)
            h, m = divmod(m, 60)
            if m:
                if h:
                    return str(h) + "时" + str(m) + "分" + str(s) + "秒"
                return str(m) + "分" + str(s) + "秒"
            return str(s) + "秒"
        return "0秒"

    def login(self):
        c_url = 'https://passport2.chaoxing.com/mlogin?' \
                'loginType=1&' \
                'newversion=true&fid=&' \
                'refer=http%3A%2F%2Foffice.chaoxing.com%2Ffront%2Fthird%2Fapps%2Fseat%2Findex'
        self.session.get(c_url).cookies.get_dict()
        data = {
            'fid': '-1',
            'uname': self.acc,
            'password': self.pwd,
            'refer': 'http%3A%2F%2Foffice.chaoxing.com%2Ffront%2Fthird%2Fapps%2Fseat%2Findex',
            't': 'true',
            'forbidotherlogin': 0,
            'validate': 0,
            'doubleFactorLogin': 0,
            'independentId': 0,
        }
        self.session.post('https://passport2.chaoxing.com/fanyalogin', data=data)
        s_url = 'https://office.chaoxing.com/front/third/apps/seat/index'
        self.session.get(s_url)

    def get_fidEnc(self):
        data = {
            'searchName': '',
            '_t': self.get_date()
        }
        res = self.session.post(url='https://i.chaoxing.com/base/cacheUserOrg', data=data)
        print(res.json()["site"][0]['schoolname'], res.json()["site"][1]['schoolname'])  # 默认显示单位的前两个名称如果是多个单位请自行修改
        for index in res.json()["site"]:
            fid = index['fid']
            res = self.session.get(url='https://uc.chaoxing.com/mobileSet/homePage?'
                                       f'fid={fid}')
            # 使用正则表达式匹配openApp()中的内容
            pattern = r'openApp\((\d+),(\d+),\'(.+?)\',\'.*?(座位|预约).*?\'\)'  # 这一步可能根据学校页面自行调整 目的是找到图书馆座位预约首页
            match = re.search(pattern, res.text)
            if match:
                mAppId = match.group(1)
                AppId = match.group(2)
                app_visit_url = "http://uc.chaoxing.com/mobile/addAppVisit"
                app_visit_data = {"mAppId": mAppId}
                self.session.post(app_visit_url, data=app_visit_data, verify=False)
                get_tally_info_url = "http://uc.chaoxing.com/mobile/getTallyInfo"
                get_tally_info_data = {"id": AppId, "mAppId": mAppId}
                get_tally_info_response = self.session.post(get_tally_info_url, data=get_tally_info_data, verify=False)
                data = get_tally_info_response.json()
                if data["status"]:
                    get_app_info_url = "http://uc.chaoxing.com/mobileSet/getAppInfo"
                    get_app_info_params = {
                        "id": AppId,
                        "mAppId": mAppId,
                        "roleId": data["roleId"],
                        "deptId": data["deptId"],
                        "fid": data["fid"],
                        "time": data["time"],
                        "enc": data["enc"]
                    }
                    app_info_response = self.session.get(get_app_info_url, params=get_app_info_params, verify=False)
                    last_url = app_info_response.json()['url']
                    last_response = self.session.get(last_url, verify=False)
                    # 每个学校的deptIdEnc值是固定的，如果是为只为你的学校提供服务请直接将deptIdEnc保存！不需要再执行get_fidEnc()方法了
                    last_location = last_response.history[2].headers['Location']
                    print(last_location)
                    self.deptIdEnc = \
                    re.compile(r'fidEnc=(.*?)&').findall(last_location)[0]
                    if self.version == 0:
                        self.seatId = re.compile("seatId=(.*?)&").findall(last_location)[0]
                        print(self.seatId)
        print(self.deptIdEnc)

    def get_seat_reservation_info(self):
        if self.version == 0:
            response = \
                self.session.get(url='https://office.chaoxing.com/data/apps/seatengine/reservelist?seatId=602').json()[
                    'data']['reserveList']
        else:
            response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/reservelist?'
                                            'indexId=0&'
                                            'pageSize=100&'
                                            'type=-1').json()['data']['reserveList']
        for index in response:
            if index['type'] == -1:
                print(index['seatNum'], index['id'], index['firstLevelName'], index['secondLevelName'],
                      index['thirdLevelName'], self.t_time(index['startTime']), self.t_time(index['endTime']),
                      self.t_second(index['learnDuration']), self.status[str(index['status'])])
            else:
                print(index['seatNum'], index['id'], index['firstLevelName'], index['secondLevelName'],
                      index['thirdLevelName'], self.t_time(index['startTime']), self.t_time(index['endTime']),
                      self.t_second(index['learnDuration']), '违约')

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
        # seatId 不一定为602 仅为演示
        if self.version == 0:
            response = \
                self.session.get(url='https://office.chaoxing.com/data/apps/seatengine/reservelist?seatId=602').json()[
                    'data']['reserveList']
        else:
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

    # 旧版系统预约
    def submit(self, seatNum, day):
        if self.version == 0:
            # 旧版不需要pageToken
            response = self.session.get(url='https://office.chaoxing.com/front/apps/seatengine/select?'
                                            'id=3833&seatId=602&fidEnc=991fe2698ebc49b9'  # 房间id roomId 可以从self.room_id_name获取 请自行发挥
                                            f'day={day}&'  # 预约时间 上下需保持一致
                                            'backLevel=2')  # 必须的参数2
            token = re.compile("token = '(.*)'").findall(response.text)[0]
            # 滑动验证码
            captcha = check.check_captcha(self.session)
            # print(captcha)
            response = self.session.get(url='https://office.chaoxing.com/data/apps/seatengine/submit?'
                                            'roomId=3833&seatId=602&'  # 房间id roomId 上下需保持一致
                                            'startTime=08%3A30&'  # 开始时间%3A代表: 自行替换9（小时）和后面00（分钟） 必须
                                            'endTime=11%3A30&'  # 结束时间 规则同上
                                            f'day={day}&'  # 预约时间 上下需保持一致
                                            f'seatNum={seatNum}&'  # 座位数字 与桌上贴纸一致
                                            f'token={token}&'
                                            f'captcha={captcha}')
            seat_result = response.json()
        else:
            response = self.session.get(url='https://office.chaoxing.com/front/apps/seat/list?'
                                            f'deptIdEnc={self.deptIdEnc}')
            pageToken = re.compile(r"&pageToken=' \+ '(.*)' \+ '&").findall(response.text)[0]
            response = self.session.get(url='https://office.chaoxing.com/front/apps/seat/select?'
                                            'id=3781&seatId=602'  # 房间id roomId 可以从self.room_id_name获取 请自行发挥
                                            f'day={day}&'  # 预约时间 上下需保持一致
                                            'backLevel=2&'  # 必须的参数2
                                            f'pageToken={pageToken}')
            token = re.compile("token: '(.*)'").findall(response.text)[0]
            response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/submit?'
                                            'roomId=3781&seatId=602&'  # 房间id roomId 上下需保持一致
                                            'startTime=20%3A30&'  # 开始时间%3A代表: 自行替换9（小时）和后面00（分钟） 必须
                                            'endTime=22%3A30&'  # 结束时间 规则同上
                                            f'day={day}&'  # 预约时间 上下需保持一致
                                            f'seatNum={seatNum}&'  # 座位数字 与桌上贴纸一致
                                            f'token={token}')
            seat_result = response.json()
        if seat_result["success"]:
            info = seat_result["data"]["seatReserve"]
            seatInfo = info["firstLevelName"] + info["secondLevelName"] + info["thirdLevelName"] + info["seatNum"]
            startTime = self.t_time(info["startTime"])
            endTime = self.t_time(info["endTime"])
            lastTime = info["duration"]
            print("预约成功! {}\n{}至{}共{}小时".format(seatInfo, startTime, endTime, lastTime))

    # 获取图书馆所有的房间和座位
    def get_all_room_and_seat(self):
        if self.deptIdEnc:
            if self.version == 0:
                # 注意 老版本的系统需要将url中的seat改为seatengine，且可能需要附带seatId的值
                response = self.session.get('https://office.chaoxing.com/data/apps/seatengine/room/list?seatId=602&'
                                            f'deptIdEnc={self.deptIdEnc}')
            else:
                response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/room/list?'
                                                f'deptIdEnc={self.deptIdEnc}')
            self.room = response.json()['data']['seatRoomList']
            deptId = self.room[0]['deptId']
            for index in self.room:
                self.room_id_capacity[index['id']] = index['capacity']
                self.room_id_name[index['id']] = index['firstLevelName'] + index['secondLevelName'] + index[
                    'thirdLevelName']
                if self.version == 0:
                    response = self.session.get(url='https://office.chaoxing.com/data/apps/seatengine/seatgrid/roomid?'
                                                    'roomId={}'.format(index['id']))
                else:
                    response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/seatgrid/roomid?'
                                                    'roomId={}'.format(index['id']))
                self.all_seat += response.json()['data']['seatDatas']
            print("座位信息获取完成")
        else:
            print("请先获取deptIdEnc")

    # 获取学习人数分布 多线程 2000座约10s
    # 注意 老版本的系统接口可能不能获取到
    def get_study_info(self):
        print("开始获取")
        q = queue.Queue()
        for item in self.all_seat:
            if item["roomId"] == 3752:
                q.put(item)
        ths = []
        for idx in range(0, 127):
            ths.append(
                threading.Thread(target=self.get_seat_info, args=(q,))
            )
        for th in ths:
            th.start()
        for th in ths:
            th.join()

    # 获取座位详细信息 配合get_study_info
    def get_seat_info(self, q: queue.Queue):
        data = ""
        while True:
            seat = q.get()
            # 注意 老版本的系统不支持此接口
            response = self.session.get(url='https://office.chaoxing.com/data/apps/seat/reserve/info?'
                                            'id={0}&seatNum={1}'.format(seat['roomId'], seat['seatNum'])).json()
            try:
                data = response["data"]
                r = data["seatReserve"]
            except:
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
    lib = Library("手机号", "密码", "版本:新版本为1/旧版本为0")
