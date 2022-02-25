help_text = f'''
本插件为战地的战绩查询插件，拥有如下指令：
--------------------
查询相关
[xxx战地1战绩or战地5战绩数据] :xxx为有效的玩家origin id
[xxx 战地1yy数据or战地5yy数据] :xxx为origin id，yy为下述详细数据，注意xxx后的空格
[/1战绩or/5战绩]or[/1yyor/5yy] :此为绑定id之后的查询指令
(战地1可查看的详细数据:战绩,武器,手枪,近战,配备(迫击炮,炸药等),特种(哨兵,喷火兵等),载具,职业,模式)
(战地5可查看的详细数据:战绩,武器,手枪,近战,配备,载具,职业)
--------------------
绑定相关
[绑定xxx] :绑定玩家origin id，更换绑定的id也同样使用本指令
[查询战地绑定] :查询自己当前绑定了哪个id
[解除战地绑定] :解除自己绑定的id
--------------------
其他相关(仅bot管理员可用)
[刷新背景图1or2] :更换完自定义背景后，在不想重启bot的情况下使用。1、2为两套图片的样式，1为背景模糊黑框不模糊，2为背景不模糊黑款模糊
'''.strip()

from requests import get
import json
import os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import io
import base64
from hoshino import Service,priv

filepath = os.path.dirname(__file__)
json_page = ""
bf1_imgpath = os.path.join(filepath, "bf1")
bfv_imgpath = os.path.join(filepath, "bfv")
bf1_bind_path = os.path.join(filepath, "bf1_bindid.json")
transtxt_path = os.path.join(filepath, "bf_translate.json")
font_path = os.path.join(filepath, "msyhl.ttc") # ""内可以换成你喜欢的字体，请在更换字体后填入字体文件名
largefont = ImageFont.truetype(font_path, 38)
middlefont = ImageFont.truetype(font_path, 30)
smallfont = ImageFont.truetype(font_path, 26)
text_list = ['击杀', '助攻', 'KD', 'KPM', '步战KD', '步战KPM', '爆头击杀', '爆头率', '精准率', '胜场', '败场', '胜率', '游戏局数', 'SPM', '技巧值', '总治疗量']
type_dict = {"weapon":"weapons", "vehicle":"vehicles", "class":"classes"}

with open(transtxt_path, 'r', encoding = 'utf-8') as f:
    bf1translate = json.loads(f.read())

# 如需更换自定义背景，请将背景重命名为background.jpg，并参照下面的说明来生成两个背景
# 自定义背景图分辨率需为1920*1080，或者与其比例一致，否则会被拉伸至该比例
def get_img():
    BGimg = Image.open(os.path.join(filepath, "background.jpg"))
    if BGimg.size != (1920, 1080):
        BGimg = BGimg.resize((1920, 1080))

    return BGimg

# 各种工具

# 缺失图片时使用本方法
def download_img(bfversion, img_type):
    json_content = ""
    if type_dict.get(img_type, "") != "":
        json_content = json_page[type_dict.get(img_type)]
    else:
        print("找不到数据")
        return

    if bfversion == "bf1":
        img_path = os.path.join(bf1_imgpath, f"{img_type}_img")
    elif bfversion == "bfv":
        img_path = os.path.join(bfv_imgpath, f"{img_type}_img")
    if img_type == "class":
        for i in json_content:
            name = i[f'{img_type}Name']
            img = i['image']
            if not os.path.exists(img_path):
                os.mkdir(img_path)
            print(f"{bfversion} 正在下载{img_type}第{json_content.index(i)+1}个图标")
            img_content = get(img).content
            with open(f"{img_path}/{name}.png", "wb")as f:
                f.write(img_content)
    else:        
        for i in json_content:
            name = i[f'{img_type}Name'].replace('/', '_')
            img = i['image']
            get_type = i['type'].replace('/', '_')
            if not os.path.exists(img_path):
                os.mkdir(img_path)
            if not os.path.exists(f"{img_path}/{get_type}"):
                os.mkdir(f"{img_path}/{get_type}")
            print(f"{bfversion} 正在下载{img_type}第{json_content.index(i)+1}个图标")
            img_content = get(img).content
            img_bytestream = io.BytesIO(img_content)
            im = Image.open(img_bytestream)

            bbox = im.getbbox()
            middle_point = ((bbox[0] + bbox[2])/2, (bbox[1] + bbox[3])/2)
            if bbox[2] - bbox[0] <= 256 and bbox[3] - bbox[1] <= 64:
                crop_box = (middle_point[0] - 128, middle_point[1] - 32, middle_point[0] + 128, middle_point[1] + 32)
            elif bbox[2] - bbox[0] > 256 and bbox[3] - bbox[1] > 64:
                crop_box = (bbox[0] - 10, bbox[1] -10, bbox[2] + 10, bbox[3] + 10)
            else:
                if bbox[2] - bbox[0] > 256:
                    crop_box = (bbox[0] - 10, middle_point[1] - 32, bbox[2] + 10, middle_point[1] + 32)
                elif bbox[3] - bbox[1] > 64:
                    crop_box = (middle_point[0] - 128, bbox[1] -10, middle_point[0] + 128, bbox[3] + 10)
            im2 = im.crop(crop_box)
            im2.save(f"{img_path}/{get_type}/{name}.png")

# 自动补全因api给出的图片数据与本地图片数据不同时缺少的图片
def img_completer(bfversion, img_type):
    if bfversion == "bf1":
        img_path = os.path.join(bf1_imgpath, f"{img_type}_img")
    elif bfversion == "bfv":
        img_path = os.path.join(bfv_imgpath, f"{img_type}_img")

    local_img_list = []
    api_img_list = []
    for i in os.walk(os.path.join(bfv_imgpath, img_type + "_img")):
        local_img_list += i[2]
    for i in range(len(local_img_list)):
        local_img_list[i] = local_img_list[i].replace(".png", "")
    api_img = json_page[type_dict.get(img_type)]
    for i in api_img:
        name = i[f'{img_type}Name'].replace('/', '_')
        api_img_list.append(name)
    a = set(api_img_list)
    b = set(local_img_list)
    compare_list = list(b ^ a)
    for i in api_img:
        name = i[f'{img_type}Name'].replace('/', '_')
        if name in compare_list:
            img = i['image']
            get_type = i['type'].replace('/', '_')
            print(f"正在补全{img_type}第{compare_list.index(name)+1}个图标")
            img_content = get(img).content
            img_bytestream = io.BytesIO(img_content)
            im = Image.open(img_bytestream)

            bbox = im.getbbox()
            middle_point = ((bbox[0] + bbox[2])/2, (bbox[1] + bbox[3])/2)
            if bbox[2] - bbox[0] <= 256 and bbox[3] - bbox[1] <= 64:
                crop_box = (middle_point[0] - 128, middle_point[1] - 32, middle_point[0] + 128, middle_point[1] + 32)
            elif bbox[2] - bbox[0] > 256 and bbox[3] - bbox[1] > 64:
                crop_box = (bbox[0] - 10, bbox[1] -10, bbox[2] + 10, bbox[3] + 10)
            else:
                if bbox[2] - bbox[0] > 256:
                    crop_box = (bbox[0] - 10, middle_point[1] - 32, bbox[2] + 10, middle_point[1] + 32)
                elif bbox[3] - bbox[1] > 64:
                    crop_box = (middle_point[0] - 128, bbox[1] -10, middle_point[0] + 128, bbox[3] + 10)
            im2 = im.crop(crop_box)
            im2.save(f"{img_path}/{get_type}/{name}.png")
    
# 更换自定义背景图后使用本方法生成一个用于展示总体战绩的背景图
def general_BGimg_creater(mode, im):
    '''
    mode为1时，新建一个背景高斯模糊，黑框半透明的图
    mode为2时，新建一个背景不模糊，黑框部分高斯模糊的图
    radius为高斯模糊的半径，可自行调整
    '''

    if mode == 1:
        im1 = im.filter(ImageFilter.GaussianBlur(radius = 3))
    elif mode == 2:
        im1 = im.copy()
    
    left_back = Image.new("RGBA", (610, 880), (0, 0, 0, 105))
    right_back = Image.new("RGBA", (1020, 190), (0, 0, 0, 105))
    bar = Image.new("RGB", (6, 95), (255, 255, 255))
    a = left_back.split()[3]
    b = right_back.split()[3]
    if mode == 2:
        left_GB = im1.crop((100, 100, 710, 980)).filter(ImageFilter.GaussianBlur(radius = 8))
        im1.paste(left_GB, (100, 100, 710, 980))

    im1.paste(left_back, (100, 100), a)
    for i in range(4):
        if mode == 2:
            right_GB = im1.crop((800, 100+40*i+190*i, 1820, 290+40*i+190*i)).filter(ImageFilter.GaussianBlur(radius = 8))
            im1.paste(right_GB, (800, 100+40*i+190*i, 1820, 290+40*i+190*i))
        im1.paste(right_back, (800, 100+40*i+190*i), b)

    for i in range(4):
        im1.paste(bar, (130, 410+140*i))
        im1.paste(bar, (130+146*1, 410+140*i))
        im1.paste(bar, (130+146*2, 410+140*i))
        im1.paste(bar, (130+146*3, 410+140*i))

    draw = ImageDraw.Draw(im1, "RGB")
    for i in range(0, len(text_list), 4):
        draw.text((141, 415+140*(i/4)), text_list[i], font = smallfont, fill = (255, 255, 255))
        draw.text((141+146*1, 415+140*(i/4)), text_list[i+1], font = smallfont, fill = (255, 255, 255))
        draw.text((141+146*2, 415+140*(i/4)), text_list[i+2], font = smallfont, fill = (255, 255, 255))
        draw.text((141+146*3, 415+140*(i/4)), text_list[i+3], font = smallfont, fill = (255, 255, 255))

    im1.save(os.path.join(filepath, "general_bg.jpg"), quality=95)

# 以及一个用于展示详细数据的背景图
def other_BGimg_creater(mode, im):
    if mode == 1:
        im1 = im.crop((430, 0, 1490, 1080)).filter(ImageFilter.GaussianBlur(radius = 3))
    elif mode == 2:
        im1 = im.crop((430, 0, 1490, 1080))
    
    back = Image.new("RGBA", (1000, 175), (0, 0, 0, 105))
    a = back.split()[3]
    for i in range(5):
        if mode == 2:
            box = im1.crop((30, 25+30*(i+1)+175*i, 1030, 200+30*(i+1)+175*i)).filter(ImageFilter.GaussianBlur(radius = 8))
            im1.paste(box, (30, 25+30*(i+1)+175*i, 1030, 200+30*(i+1)+175*i))
        im1.paste(back, (30, 25+30*(i+1)+175*i), a)
    
    im1.save(os.path.join(filepath, "other_bg.jpg"), quality=95)

# 转换秒数为时分秒的形式
def seconds_trans(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
   
    return "%02d时%02d分%02d秒" % (h, m, s)

def resize_font(font_size, text_str, limit_width):
    '''
    在给定的长度内根据文字内容来改变文字的字体大小
    font_size为默认大小，即如果函数判断以此字体大小所绘制出来的文字内容不会超过给定的长度时，则保持这个大小
    若绘制出来的文字内容长度大于给定长度，则会不断对减小字体大小直至刚好小于给定长度
    text_str为文字内容
    limit_width为给定的长度
    返回内容为PIL.ImageFont.FreeTypeFont对象
    '''

    font = ImageFont.truetype(font_path, font_size)
    font_lenth = font.getsize(str(text_str))[0]
    while font_lenth > limit_width:
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)
        font_lenth = font.getsize(text_str)[0]

    return font

def get_data(bfversion, player_name):
    global json_page
    if bfversion == "bf1":
        surl = f"https://api.gametools.network/bf1/all/?name={player_name}&lang=en-us"
    elif bfversion == "bfv":
        surl = f"https://api.gametools.network/bfv/all/?name={player_name}&lang=en-us"
    reqs = get(surl).text
    json_page = json.loads(reqs)
    
    return json_page

def general():
    general_dict = {}
    general_dict['击杀'] = json_page['kills']
    general_dict['助攻'] = int(json_page['killAssists'])
    general_dict['KD'] = json_page['killDeath']
    general_dict['KPM'] = json_page['killsPerMinute']
    general_dict['步战KD'] = json_page['infantryKillDeath']
    general_dict['步战KPM'] = json_page['infantryKillsPerMinute']
    general_dict['爆头击杀'] = json_page['headShots']
    general_dict['爆头率'] = json_page['headshots']
    general_dict['精准率'] = json_page['accuracy']
    general_dict['胜场'] = json_page['wins']
    general_dict['败场'] = json_page['loses']
    general_dict['胜率'] = json_page['winPercent']
    general_dict['游戏局数'] = json_page['roundsPlayed'] 
    general_dict['SPM'] = json_page['scorePerMinute']
    general_dict['技巧值'] = json_page['skill']
    general_dict['总治疗量'] = int(json_page['heals'])
    general_dict['昵称'] = json_page['userName']
    general_dict['等级'] = json_page['rank']
    general_dict['游玩时间'] = seconds_trans(json_page['secondsPlayed'])
    general_dict['头像img'] = json_page['avatar']
    
    return general_dict

def best_class():
    class_lsit = []
    class_page = json_page['classes']
    for i in class_page:
        class_dict = {}
        class_dict['名称'] = i['className']
        class_dict['击杀'] = i['kills']
        class_dict['KPM'] = i['kpm']
        class_dict['得分'] = i['score']
        class_dict['时长'] = seconds_trans(i['secondsPlayed'])
        class_lsit.append(class_dict)
    class_lsit.sort(key = lambda x : x['击杀'], reverse=True)
    
    return class_lsit

def best_weapon():
    general_weapon_list, Gadget_list, Sidearm_list, Field_kit_list, Melee_list = [], [], [], [], []
    weapon_page = json_page['weapons']
    for i in weapon_page:
        weapon_dict = {}
        weapon_dict['名称'] = i['weaponName'].replace('/', '_')
        weapon_dict['击杀'] = i['kills']
        weapon_dict['KPM'] = i['killsPerMinute']
        weapon_dict['爆头率'] = i['headshots']
        weapon_dict['精准率'] = i['accuracy']
        weapon_dict['时长'] = seconds_trans(i['timeEquipped'])
        weapon_dict['类型'] = i['type'].replace('/', '_')
        general_weapon_list.append(weapon_dict)
    general_weapon_list.sort(key = lambda x : x['击杀'], reverse=True)
    Gadget_list.extend(i for i in general_weapon_list if i.get('类型') == "Gadget")
    Sidearm_list.extend(i for i in general_weapon_list if i.get('类型') == "Sidearm")
    Field_kit_list.extend(i for i in general_weapon_list if i.get('类型') == "Field kit")
    Melee_list.extend(i for i in general_weapon_list if i.get('类型') == "Melee")

    return general_weapon_list, Gadget_list, Sidearm_list, Field_kit_list, Melee_list

def best_vehicles():
    vehicle_lsit = []
    vehicle_page = json_page['vehicles']
    for i in vehicle_page:
        vehicle_dict = {}
        vehicle_dict['击杀'] = i['kills']
        vehicle_dict['KPM'] = i['killsPerMinute']
        vehicle_dict['时长'] = seconds_trans(i['timeIn'])
        vehicle_dict['类型'] = i['type'].replace('/', '_')
        vehicle_dict['名称'] = i['vehicleName'].replace('/', '_')
        vehicle_lsit.append(vehicle_dict)
    vehicle_lsit.sort(key = lambda x : x['击杀'], reverse=True)
    
    return vehicle_lsit

def best_gamemodes():
    modes_list = []
    modes_page = json_page['gamemodes']
    for i in modes_page:
        modes_dict = {}
        modes_dict['胜场'] = i['wins']
        modes_dict['败场'] = i['losses']
        modes_dict['胜率'] = i['winPercent']
        modes_dict['得分'] = i['score']
        modes_dict['名称'] = i['gamemodeName']
        modes_list.append(modes_dict)
    modes_list.sort(key = lambda x : x['得分'], reverse=True)
    
    return modes_list

# 返回文字内容（除去名称和类型）以及文字内容的长度
def dict_text_draw_info(select_dict):
    text = ""
    text_lenth = 0
    for k,v in select_dict.items():
        if k == "名称" or k == '类型':
            continue
        text += f'{k}:{str(v)}   '

    font = resize_font(38, text, 1000)
    text_lenth = font.getsize(text.strip())[0]

    return text, text_lenth

# 返回图标路径，图标透明度，将图标宽度拉至100像素后对应的长度，图标名称
def icon_info(bfversion, mode, dict):
    if bfversion == "bf1":
        img_path = bf1_imgpath
    elif bfversion == "bfv":
        img_path = bfv_imgpath
    icon_name = dict.get('名称')
    try:
        if mode == "class":
            im = Image.open(os.path.join(img_path, 'class_img', icon_name + '.png'))
        elif mode == "weapon":
            im = Image.open(os.path.join(img_path, 'weapon_img', dict.get('类型'), icon_name + '.png'))
        elif mode == "vehicle":
            im = Image.open(os.path.join(img_path, 'vehicle_img', dict.get('类型'), icon_name + '.png'))
    except FileNotFoundError:
        raise Exception(mode)
    size = im.size
    x, y = int(size[0]*(100/size[1])), 100
    icon_path = im.resize((x, y))

    return icon_path, icon_path.split()[3], x, icon_name.replace('_', '/')

# 将详细数据绘制到图片中
def bestinfo_drawer(bfversion, mode, image, dict, middle_x, y, blank):
    icon1 = icon_info(bfversion, mode, dict)
    image.paste(icon1[0], (middle_x-icon1[2]-20, y), icon1[1])
    draw = ImageDraw.Draw(image, "RGB")
    transtext = bf1translate.get(str(icon1[3]).upper(), icon1[3])
    draw.text((middle_x+20, y+25), transtext, font = resize_font(38, transtext, 490), fill = (255, 255, 255))
    draw1 = dict_text_draw_info(dict)
    draw.text((middle_x-draw1[1]/2, y+blank+100), draw1[0], font = resize_font(38, draw1[0], 1000), fill = (255, 255, 255))

# 生成总体战绩图片的方法
def general_img_creater(bfversion, g_dict, c_list, w_list, v_list, g_list):
    im = Image.open(os.path.join(filepath, "general_bg.jpg"))
    a = get(g_dict.get('头像img')).content
    aimg_bytestream = io.BytesIO(a)
    a_imgb = Image.open(aimg_bytestream).resize((230, 230))
    im.paste(a_imgb, (130, 130))
    draw = ImageDraw.Draw(im, "RGB")

    draw.text((370, 130), g_dict.get('昵称'), font = resize_font(38, g_dict.get('昵称'), 240), fill = (255, 255, 255))
    draw.text((370, 220), f"等级:{str(g_dict.get('等级'))}", font = largefont, fill = (255, 255, 255))
    draw.text((370, 310), f"时长:{g_dict.get('游玩时间')}", font = middlefont, fill = (255, 255, 255))

    for i in range(0, 16, 4):
        draw.text((141, 455+140*(i/4)), str(g_dict.get(text_list[i])), font = resize_font(30, g_dict.get(text_list[i]), 130), fill = (255, 255, 255))
        draw.text((141+146*1, 455+140*(i/4)), str(g_dict.get(text_list[i+1])), font = resize_font(30, g_dict.get(text_list[i+1]), 130), fill = (255, 255, 255))
        draw.text((141+146*2, 455+140*(i/4)), str(g_dict.get(text_list[i+2])), font = resize_font(30, g_dict.get(text_list[i+2]), 130), fill = (255, 255, 255))
        draw.text((141+146*3, 455+140*(i/4)), str(g_dict.get(text_list[i+3])), font = resize_font(30, g_dict.get(text_list[i+3]), 130), fill = (255, 255, 255))
    
    best_class_dict = c_list[0]
    best_weapon_dict = w_list[0]
    best_vehicles_dict = v_list[0]
    best_gamemodes_dict = g_list[0]

    bestinfo_drawer(bfversion, 'class', im, best_class_dict, 1310, 115, 10)
    bestinfo_drawer(bfversion, 'weapon', im, best_weapon_dict, 1310, 115+230*1, 10)
    bestinfo_drawer(bfversion, 'vehicle', im, best_vehicles_dict, 1310, 115+230*2, 10)
    if bfversion == "bf1":
        draw1 = dict_text_draw_info(best_gamemodes_dict)
        modename = f"最佳游戏模式:{bf1translate.get(best_gamemodes_dict.get('名称').upper(), best_gamemodes_dict.get('名称'))}"
        draw.text((1310-largefont.getsize(modename)[0]/2, 110+230*3+25), modename, font =largefont, fill = (255, 255, 255))
        draw.text((1310-draw1[1]/2, 110+230*3+115), draw1[0], font = resize_font(38, draw1[0], 1000), fill = (255, 255, 255))
    elif bfversion == "bfv":
        bestinfo_drawer(bfversion, 'weapon', im, g_list[0], 1310, 115+230*3, 10)

    b_io = io.BytesIO()
    im.save(b_io, format = "JPEG")
    base64_str = 'base64://' + base64.b64encode(b_io.getvalue()).decode()

    return base64_str

# 生成详细数据图片的方法
def other_img_creater(bfversion, mode, best_list, playname):
    im = Image.open(os.path.join(filepath, "other_bg.jpg"))
    draw = ImageDraw.Draw(im, "RGB")
    if mode == "gamemode":
        for i in range(5):
            draw1 = dict_text_draw_info(best_list[i])
            modename = f"游戏模式:{bf1translate.get(best_list[i].get('名称').upper(), best_list[i].get('名称'))}"
            draw.text((530-largefont.getsize(modename)[0]/2, 85+175*i+30*i), modename, font = largefont, fill = (255, 255, 255))
            draw.text((530-draw1[1]/2, 160+175*i+30*i), draw1[0], font = resize_font(38, draw1[0], 980), fill = (255, 255, 255))
    else:
        if bfversion == "bfv" and mode == "class":
            cycles = 4
        else:
            cycles = 5
        for i in range(cycles):
            best_dict = best_list[i]
            bestinfo_drawer(bfversion, mode, im, best_dict, 530, 65+175*i+30*i, 10)
    
    draw.text((530-largefont.getsize(playname)[0]/2, 0), playname, font = largefont, fill = (0, 0, 0))

    b_io = io.BytesIO()
    im.save(b_io, format = "JPEG")
    base64_str = 'base64://' + base64.b64encode(b_io.getvalue()).decode()

    return base64_str

# 绑定id
def bindid_action(mode, userqqid, playername):
    bindid_dict = {}
    if not os.path.exists(bf1_bind_path):
        with open(bf1_bind_path, "w", encoding = "utf-8") as f:
            f.write(json.dumps(bindid_dict))
    with open(bf1_bind_path, "r", encoding = "utf-8") as f:
        id_dict = json.loads(f.read())
    oldid = id_dict.get(str(userqqid), '')
    if mode == 'add':
        newid = str(playername)
        id_dict[str(userqqid)] = str(playername)
    elif mode == 'delete':
        id_dict.pop(str(userqqid), '')
        newid = ''
    with open(bf1_bind_path, "w+", encoding = "utf-8") as f:
        f.write(json.dumps(id_dict))
    return oldid, newid

def mode_dict_creater():
    get_weapon = best_weapon()[0]
    get_gadget = best_weapon()[1]
    get_sidearm = best_weapon()[2]
    get_field_kit = best_weapon()[3]
    get_melee = best_weapon()[4]
    get_vehicle = best_vehicles()
    get_class = best_class()
    try:
        get_gamemode = best_gamemodes()
    except:
        get_gamemode = []

    mode_dict = {"武器":("weapon", get_weapon), "配备":("weapon", get_gadget), "手枪":("weapon", get_sidearm), "特种":("weapon", get_field_kit),\
         "近战":("weapon", get_melee), "载具":("vehicle", get_vehicle), "职业":("class", get_class), "模式":("gamemode", get_gamemode)}
    return mode_dict

sv = Service("zhandi_query")

@sv.on_suffix('战绩数据')
async def bf_general_query(bot, ev):
    mes_id = ev['message_id']
    mes = ev.message.extract_plain_text().strip()
    playername = mes[0:-3]
    if "战地1" in mes:
        bfversion = "bf1"
    elif "战地5" in mes:
        bfversion = "bfv"
    else:
        # await bot.send(ev, f"[CQ:reply,id={mes_id}]请指定战地版本(战地1或战地5)")
        return
    resp = get_data(bfversion, playername)
    if "Player not found" in str(resp.values()) or "playername not found" in str(resp.values()):
        await bot.send(ev, f"[CQ:reply,id={mes_id}]查无此人，可能原因为:此id无效，或游戏库中没有对应版本战地游戏，或者查询的api抽风，这个情况可能需要过几天才会恢复")
    elif "Internal Server Error" in str(resp.values()):
        await bot.send(ev, "api服务器炸了")
    else:
        dict = general()
        try:
            if "战地1" in mes:
                img_mes = general_img_creater(bfversion, dict, best_class(), best_weapon()[0], best_vehicles(), best_gamemodes())
                await bot.send(ev, f"[CQ:reply,id={mes_id}][CQ:image,file={img_mes}]")
            elif "战地5" in mes:
                img_mes = general_img_creater(bfversion, dict, best_class(), best_weapon()[0], best_vehicles(), best_weapon()[4])
                await bot.send(ev, f"[CQ:reply,id={mes_id}][CQ:image,file={img_mes}]")
        except Exception as e:
            if str(e) == "weapon" or str(e) == "vehicle" or str(e) == "class":
                await bot.send(ev, "检测到图片缺失,将启动自动补全,请在完成后再次发送指令")
                img_completer(bfversion, str(e))
                await bot.send(ev, "补全完成,请重新发送指令！")
            else:
                await bot.send(ev, f"发生了其他错误，报错内容为:{e}")

@sv.on_suffix('数据')
async def bf_other_query(bot, ev):
    mes_id = ev['message_id']
    mes = ev.message.extract_plain_text().strip().split()
    playername = mes[0]
    if "战地1" in mes[1]:
        bfversion = "bf1"
    elif "战地5" in mes[1]:
        bfversion = "bfv"
    else:
        # await bot.send(ev, f"[CQ:reply,id={mes_id}]请指定战地版本(战地1或战地5)")
        return
    mode = mes[1][3:]
    resp = get_data(bfversion, playername)
    if "Player not found" in str(resp.values()) or "playername not found" in str(resp.values()):
        await bot.send(ev, f"[CQ:reply,id={mes_id}]查无此人，可能原因为:此id无效，或游戏库中没有对应版本战地游戏，或者查询的api抽风，这个情况可能需要过几天才会恢复")
    elif "Internal Server Error" in str(resp.values()):
        await bot.send(ev, "api服务器炸了")
    else:
        query_mode = mode_dict_creater().get(mode)[0]
        query_list = mode_dict_creater().get(mode)[1]
        try:
            img_mes = other_img_creater(bfversion, query_mode, query_list, playername)
            await bot.send(ev, f"[CQ:reply,id={mes_id}][CQ:image,file={img_mes}]")
        except Exception as e:
            if str(e) == "weapon" or str(e) == "vehicle" or str(e) == "class":
                await bot.send(ev, "检测到图片缺失,将启动自动补全,请在完成后再次发送指令")
                img_completer(bfversion, str(e))
                await bot.send(ev, "补全完成,请重新发送指令！")
            else:
                await bot.send(ev, f"发生了其他错误，报错内容为:{e}")

@sv.on_prefix('绑定')
async def bf_bind(bot, ev):
    userqqid = ev['user_id']
    playername = ev['message'][0]['data']['text']
    bind_stat = bindid_action("add", userqqid, playername)
    if bind_stat[0] == "":
        await bot.send(ev, f"绑定成功!新id:{bind_stat[1]}", at_sender=True)
    elif bind_stat[0] != "":
        await bot.send(ev, f"替换绑定成功!旧id:{bind_stat[0]}->新id:{bind_stat[1]}", at_sender=True)

@sv.on_fullmatch('查询战地绑定')
async def bindid_query(bot, ev):
    with open(bf1_bind_path, "r", encoding = "utf-8") as f:
        id_dict = json.loads(f.read())
    bind_stat = id_dict.get(str(ev['user_id']), '')
    if bind_stat == '':
        await bot.send(ev, "您目前未绑定任何id!", at_sender=True)
    else:
        await bot.send(ev, f"您目前绑定的id:{bind_stat}", at_sender=True)

@sv.on_fullmatch('解除战地绑定')
async def bf_unbind(bot, ev):
    userqqid = ev['user_id']
    bind_stat = bindid_action("delete", userqqid, None)
    if bind_stat[0] == '':
        await bot.send(ev, "您还未绑定任何id!", at_sender=True)
    else:
        await bot.send(ev, f"解绑id:{bind_stat[0]}成功!", at_sender=True)

@sv.on_prefix('/')
async def bind_search(bot, ev):
    mes = ev.message.extract_plain_text().strip()
    mes_id = ev['message_id']
    with open(bf1_bind_path, "r", encoding = "utf-8") as f:
        id_dict = json.loads(f.read())
    if id_dict.get(str(ev['user_id']), '') == '' and ("1" in mes[0] or "5" in mes[0]):
        await bot.send(ev, f"[CQ:reply,id={mes_id}]您暂未绑定id，请发送绑定+id进行绑定!")
    else:
        if "1" in mes[0]:
            bfversion = "bf1"
        elif "5" in mes[0]:
            bfversion = "bfv"
        else:
            # await bot.send(ev, f"[CQ:reply,id={mes_id}]请指定战地版本(/1或/5)")
            return
        playername = id_dict.get(str(ev['user_id']), '')
        resp = get_data(bfversion, playername)
        mode = mes[1:]
        if "Player not found" in str(resp.values()) or "playername not found" in str(resp.values()):
            await bot.send(ev, f"[CQ:reply,id={mes_id}]查无此人，可能原因为:此id无效，或游戏库中没有对应版本战地游戏，或者查询的api抽风，这个情况可能需要过几天才会恢复")
        elif "Internal Server Error" in str(resp.values()):
            await bot.send(ev, "api服务器炸了")
        else:
            dict = general()
            if mode == "战绩":
                try:
                    if "1" in mes:
                        img_mes = general_img_creater(bfversion, dict, best_class(), best_weapon()[0], best_vehicles(), best_gamemodes())
                        await bot.send(ev, f"[CQ:reply,id={mes_id}][CQ:image,file={img_mes}]")
                    elif "5" in mes:
                        img_mes = general_img_creater(bfversion, dict, best_class(), best_weapon()[0], best_vehicles(), best_weapon()[4])
                        await bot.send(ev, f"[CQ:reply,id={mes_id}][CQ:image,file={img_mes}]")
                except Exception as e:
                    if str(e) == "weapon" or str(e) == "vehicle" or str(e) == "class":
                        await bot.send(ev, "检测到图片缺失,将启动自动补全,请在完成后再次发送指令")
                        img_completer(bfversion, str(e))
                        await bot.send(ev, "补全完成,请重新发送指令！")
                    else:
                        await bot.send(ev, f"发生了其他错误，报错内容为:{e}")
            else:
                query_mode = mode_dict_creater().get(mode)[0]
                query_list = mode_dict_creater().get(mode)[1]
                try:
                    img_mes = other_img_creater(bfversion, query_mode, query_list, playername)
                    await bot.send(ev, f"[CQ:reply,id={mes_id}][CQ:image,file={img_mes}]")
                except Exception as e:
                    await bot.send(ev, "检测到图片缺失,将启动自动补全,请在完成后再次发送指令")
                    img_completer(bfversion, str(e))
                    await bot.send(ev, "补全完成,请重新发送指令！")

@sv.on_prefix('刷新背景图')
async def refresh_BGimg(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, "本功能只对bot管理员开放")
        return
    mode = ev.message.extract_plain_text().strip()
    general_BGimg_creater(int(mode), get_img())
    other_BGimg_creater(int(mode), get_img())
    await bot.send(ev, "刷新完毕")

@sv.on_fullmatch('战地插件帮助')
async def bot_help(bot, ev):
    await bot.send(ev, help_text)
