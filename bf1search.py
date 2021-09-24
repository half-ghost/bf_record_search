help_text = f'''
本插件为战地1的战绩查询插件，拥有如下指令：
[xxx战绩]xxx为有效的玩家origin id
[xxx 武器or载具or模式or职业数据]注意空格
[更新图片资源xxx]仅在缺少图片资源时使用，xxx为有效的玩家origin id
[刷新背景图1or2]更换完自定义背景后，在不想重启bot的情况下使用
1、2为两套图片的样式，1为背景模糊黑框不模糊，2为背景不模糊黑款模糊
'''.strip()

from requests import get
import json
import os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import io
import base64
from hoshino import Service


filepath = os.path.dirname(__file__)
json_page = ""
font_path = os.path.join(filepath, "msyhl.ttc") # ""内可以换成你喜欢的字体，请在更换字体后填入字体文件名
largefont = ImageFont.truetype(font_path, 38)
middlefont = ImageFont.truetype(font_path, 30)
smallfont = ImageFont.truetype(font_path, 26)
text_list = ['击杀', '助攻', 'KD', 'KPM', '步战KD', '步战KPM', '爆头击杀', '爆头率', '精准率', '胜场', '败场', '胜率', '游戏局数', 'SPM', '技巧值', '总治疗量']

# 如需更换自定义背景，请将背景重命名为background.jpg，并参照下面的说明来生成两个背景
# 自定义背景图分辨率需为1920*1080，或者与其比例一致，否则会被拉伸至该比例
BGimg = Image.open(os.path.join(filepath, "background.jpg"))
if BGimg.size != (1920, 1080):
    BGimg = BGimg.resize((1920, 1080))

# 各种工具

# 缺失图片时使用本方法
def download_img(img_type):
    json_content = ""
    if img_type == "weapon":
        json_content = json_page['weapons']
    elif img_type == "vehicle":
        json_content = json_page['vehicles']
    elif img_type == "class":
        json_content = json_page['classes']
    else:
        print("找不到数据")
        return
    img_path = os.path.join(filepath, f"{img_type}_img")
    if img_type == "class":
        for i in json_content:
            name = i[f'{img_type}Name']
            img = i['image']
            if not os.path.exists(img_path):
                os.mkdir(img_path)
            print(f"正在下载{img_type}第{json_content.index(i)+1}个图标")
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
            print(f"正在下载{img_type}第{json_content.index(i)+1}个图标")
            img_content = get(img).content
            with open(f"{img_path}/{get_type}/{name}.png", "wb")as f:
                f.write(img_content)

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
            box = im1.crop((30, 25+30*(i+1)+175*i)).filter(ImageFilter.GaussianBlur(radius = 8))
            im1.paste(box, (30, 25+30*(i+1)+175*i))
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

def get_data(player_name):
    global json_page
    surl = f"https://api.gametools.network/bf1/all/?name={player_name}&lang=en-us"
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
    weapon_list = []
    weapon_page = json_page['weapons']
    for i in weapon_page:
        weapon_dict = {}
        weapon_dict['名称'] = i['weaponName'].replace('/', '_')
        weapon_dict['击杀'] = i['kills']
        weapon_dict['KPM'] = i['killsPerMinute']
        weapon_dict['爆头击杀'] = i['headshots']
        weapon_dict['精准率'] = i['accuracy']
        weapon_dict['类型'] = i['type'].replace('/', '_')
        weapon_list.append(weapon_dict)
    weapon_list.sort(key = lambda x : x['击杀'], reverse=True)
    
    return weapon_list

def best_vehicles():
    vehicle_lsit = []
    vehicle_page = json_page['vehicles']
    for i in vehicle_page:
        vehicle_dict = {}
        vehicle_dict['击杀'] = i['kills']
        vehicle_dict['KPM'] = i['killsPerMinute']
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

def dict_text_draw_info(select_dict):
    text = ""
    text_width = 0
    for k,v in select_dict.items():
        if k == "名称" or k == '类型':
            continue
        text += f'{k}:{str(v)}   '

    font = resize_font(38, text, 1000)
    text_width = font.getsize(text.strip())[0]

    return text, text_width

def icon_info(mode, dict):
    icon_name = dict.get('名称')
    if mode == "class":
        im = Image.open(os.path.join(filepath, 'class_img', icon_name + '.png', ))
    elif mode == "weapon":
        im = Image.open(os.path.join(filepath, 'weapon_img', dict.get('类型'), icon_name + '.png', ))
    elif mode == "vehicle":
        im = Image.open(os.path.join(filepath, 'vehicle_img', dict.get('类型'), icon_name + '.png', ))
    
    size = im.size
    x, y = int(size[0]*(100/size[1])), 100
    icon_path = im.resize((x, y))

    return icon_path, icon_path.split()[3], x, icon_name

def bestinfo_drawer(mode, image, dict, middle_x, y, blank):
    if mode == 'class':
        icon1 = icon_info('class', dict)
    if mode == 'weapon':
        icon1 = icon_info('weapon', dict)
    if mode == 'vehicle':
        icon1 = icon_info('vehicle', dict)

    image.paste(icon1[0], (middle_x-icon1[2]-20, y), icon1[1])
    draw = ImageDraw.Draw(image, "RGB")
    draw.text((middle_x+20, y+25), icon1[3].replace('_', '/'), font = resize_font(38, icon1[3].replace('_', '/'), 490), fill = (255, 255, 255))
    draw1 = dict_text_draw_info(dict)
    draw.text((middle_x-draw1[1]/2, y+blank+100), draw1[0], font = resize_font(38, draw1[0], 1000), fill = (255, 255, 255))

# 生成总体战绩图片的方法
def general_img_creater(g_dict, c_list, w_list, v_list, g_list):
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

    bestinfo_drawer('class', im, best_class_dict, 1310, 115, 10)
    bestinfo_drawer('weapon', im, best_weapon_dict, 1310, 115+230*1, 10)
    bestinfo_drawer('vehicle', im, best_vehicles_dict, 1310, 115+230*2, 10)
    draw1 = dict_text_draw_info(best_gamemodes_dict)
    modename = f"最佳游戏模式:{best_gamemodes_dict.get('名称')}"
    draw.text((1310-largefont.getsize(modename)[0]/2, 110+230*3+25), modename, font =largefont, fill = (255, 255, 255))
    draw.text((1310-draw1[1]/2, 110+230*3+115), draw1[0], font = resize_font(38, draw1[0], 1000), fill = (255, 255, 255))

    b_io = io.BytesIO()
    im.save(b_io, format = "JPEG")
    base64_str = 'base64://' + base64.b64encode(b_io.getvalue()).decode()

    return base64_str

# 生成详细数据图片的方法
def other_img_creater(mode, best_list, palyername):
    im = Image.open(os.path.join(filepath, "other_bg.jpg"))
    draw = ImageDraw.Draw(im, "RGB")
    if mode == "gamemode":
        for i in range(5):
            draw1 = dict_text_draw_info(best_list[i])
            modename = f"游戏模式:{best_list[i].get('名称')}"
            draw.text((530-largefont.getsize(modename)[0]/2, 85+175*i+30*i), modename, font = largefont, fill = (255, 255, 255))
            draw.text((530-draw1[1]/2, 160+175*i+30*i), draw1[0], font = resize_font(38, draw1[0], 980), fill = (255, 255, 255))
    else:
        for i in range(5):
            best_dict = best_list[i]
            bestinfo_drawer(mode, im, best_dict, 530, 65+175*i+30*i, 10)
    
    draw.text((530-largefont.getsize(palyername)[0]/2, 0), palyername, font = largefont, fill = (0, 0, 0))

    b_io = io.BytesIO()
    im.save(b_io, format = "JPEG")
    base64_str = 'base64://' + base64.b64encode(b_io.getvalue()).decode()

    return base64_str

# 首次加载时，生成两个背景，默认为模式1
# 若需要更换自定义背景，请在图片重命名之后重启本插件
# 在首次加载生成背景之后，最好将这部分代码注释掉，下次需要时再使用
general_BGimg_creater(1, BGimg)
other_BGimg_creater(1, BGimg)

# 首次加载时如果没有3个图标文件夹，则自动下载
# 如果需要下载图标文件，则在get_data("")内填入任意一个库存内有对应战地版本游戏的origin的id
# 首次加载下载完图片后，最好将这部分代码注释掉，下次需要时再使用
# get_data("")
# if not os.path.exists(os.path.join(filepath, "class_img")):
#     download_img("class")
# if not os.path.exists(os.path.join(filepath, "weapon_img")):
#     download_img("weapon")
# if not os.path.exists(os.path.join(filepath, "vehicle_img")):
#     download_img("vehicle")

sv = Service("zhandi_query")

@sv.on_suffix('战绩')
async def zd_general_query(bot, ev):
    player = ev.message.extract_plain_text().strip()
    resp = get_data(player)
    if resp.get("detail", " ") == "playername not found":
        await bot.send(ev, "查无此人")
    else:
        dict = general()
        img_mes = general_img_creater(dict, best_class(), best_weapon(), best_vehicles(), best_gamemodes())
        await bot.send(ev, f"[CQ:image,file={img_mes}]")

@sv.on_suffix('数据')
async def zd_other_query(bot, ev):
    evmes = ev.message.extract_plain_text().strip().split(" ")
    playername = evmes[0]
    mode =evmes[1]
    resp = get_data(playername)
    if resp.get("detail", " ") == "playername not found":
        await bot.send(ev, "查无此人")
    else:
        if mode == "武器":
            query_mode = "weapon"
            query_list = best_weapon()
        elif mode == "载具":
            query_mode = "vehicle"
            query_list = best_vehicles()
        elif mode == "职业":
            query_mode = "class"
            query_list = best_class()
        elif mode == "模式":
            query_mode = "gamemode"
            query_list = best_gamemodes()
        img_mes = other_img_creater(query_mode, query_list, playername)
        await bot.send(ev, f"[CQ:image,file={img_mes}]")

@sv.on_prefix('更新图片资源')
async def refresh_img(bot, ev):
    palyername = ev.message.extract_plain_text().strip()
    resp = get_data(palyername)
    if resp.get("detail", " ") == "playername not found":
        await bot.send(ev, "此id无效，请输入其他有效id")
    else:
        await bot.send(ev, "正在更新图片资源，请等待更新完毕后再使用本插件")
        if not os.path.exists(os.path.join(filepath, "class_img")):
            download_img("class")
        if not os.path.exists(os.path.join(filepath, "weapon_img")):
            download_img("weapon")
        if not os.path.exists(os.path.join(filepath, "vehicle_img")):
            download_img("vehicle")
        await bot.send(ev, "更新图片资源完毕")

@sv.on_prefix('刷新背景图')
async def refresh_BGimg(bot, ev):
    mode = ev.message.extract_plain_text().strip()
    BGimg1 = Image.open(os.path.join(filepath, "background.jpg"))
    if BGimg1.size != (1920, 1080):
        BGimg1 = BGimg1.resize((1920, 1080))
    general_BGimg_creater(mode, BGimg1)
    other_BGimg_creater(mode, BGimg)
    await bot.send(ev, "刷新完毕")

@sv.on_fullmatch('战地战绩插件帮助')
async def bot_help(bot, ev):
    await bot.send(ev, help_text)
