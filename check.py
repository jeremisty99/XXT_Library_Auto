import json
import re
import ddddocr
import requests
import execjs


def check_captcha(session):
    with open('./generateCaptchaKey.js', encoding='utf-8') as f:
        js = f.read()

    # 通过compile命令转成一个js对象
    docjs = execjs.compile(js)

    # 调用function
    res = docjs.call('generateCaptchaKey')
    ckey = res['captchaKey']
    token = res['token']

    data = {
        'callback': "callback",
        'captchaId': "42sxgHoTPTKbt0uZxPJ7ssOvtXr3ZgZ1",
        'type': "slide",
        'version': "1.1.14",
        'captchaKey': ckey,
        'token': token,
        'referer': "https://office.chaoxing.com/front/third/apps/seatengine/select",
    }
    res = session.post('http://captcha.chaoxing.com/captcha/get/verification/image', data=data)
    print(res.text)
    captcha_data = json.loads(re.search(r'\{.*\}', res.text)[0])
    background = requests.get(captcha_data["imageVerificationVo"]["shadeImage"]).content
    target = requests.get(captcha_data["imageVerificationVo"]["cutoutImage"]).content
    token_new = captcha_data["token"]

    det = ddddocr.DdddOcr(det=False, ocr=False)
    res_det = det.slide_match(target, background)

    print(res_det['target'])

    data_check = {
        "callback": "callback",
        "captchaId": "42sxgHoTPTKbt0uZxPJ7ssOvtXr3ZgZ1",
        "type": "slide",
        "token": token_new,
        "textClickArr": ('[{{\"x\":{x}}}]').format(x=res_det['target'][0]),
        "coordinate": "[]",
        "runEnv": "10",
        "version": "1.1.14"
    }

    res_check = session.get(
        "http://captcha.chaoxing.com/captcha/check/verification/result", params=data_check, headers={
            "Referer": "http://office.chaoxing.com/",
        })

    check_result = json.loads(re.search(r'\{.*\}', res_check.text)[0])
    print(check_result['result'])
    if check_result['result']:
        return json.loads(check_result['extraData'])['validate']
    else:
        print('error')
        return res_check.text
