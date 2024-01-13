from PIL import Image
from PIL import ImageEnhance
from PIL import ImageSequence
from PIL import Image
from collections import Counter
import qrcode
import pyshorteners



# 画像中の黒色を指定されたカスタムカラーで置き換えるための関数
def color_replace(image, color):
    """Replace black with other color

    :color: custom color (r,g,b,a)
    :image: image to replace color
    :returns: TODO

    """
    # 画像のピクセルデータをロード
    pixels = image.load()
    # 画像の幅（横のピクセル数）を取得
    size = image.size[0]

    # 画像内のすべてのピクセルに対してループ
    for width in range(size):
        for height in range(size):
            # ピクセルのRGB値とアルファ値（透明度）を取得
            r, g, b, a = pixels[width, height]

            # もしピクセルが黒色であれば（RGBが0, 0, 0, 255であれば）
            if (r, g, b, a) == (0,0,0,255):
                # 指定されたカスタムカラーで置き換えます
                pixels[width,height] = color
            else:
                # アルファ値を除くRGB値は元のままで
                # アルファ値だけ指定されたカスタムカラーのアルファ値に置き換えます
                pixels[width,height] = (r,g,b,color[3])



# QRコードを生成し、指定された画像と組み合わせるための関数
def produce(txt,img,ver=5,err_crt = qrcode.constants.ERROR_CORRECT_H,bri = 1.0, cont = 1.0,\
        colourful = False, rgba = (0,0,0,255),pixelate = False):

    # 関数を呼び出し、各フレームの画像をリストとして返す
    """Produce QR code
    :txt: QR text
    :img: Image path / Image object
    :ver: QR version
    :err_crt: QR error correct
    :bri: Brightness enhance
    :cont: Contrast enhance
    :colourful: If colourful mode
    :rgba: color to replace black
    :pixelate: pixelate
    :returns: list of produced image

    """


    # もしimgが文字列であれば、Image.open()で画像を開いてimgに代入
    if type(img) is str:
        img = Image.open(img)

    # もしimgがImage.Imageオブジェクトであれば、何もせず進む
    elif type(img) is Image.Image:
        pass

    # それ以外の場合は、空のリストを返して関数を終了します
    else:
        return []
    # ImageSequence.Iteratorを使用して画像の各フレームに対してproduce_impl関数を呼び出し、リストに追加
    frames = [produce_impl(txt,frame.copy(),ver,err_crt,bri,cont,colourful,rgba,pixelate) for frame in ImageSequence.Iterator(img)]
    # 生成された画像フレームのリストを返す
    return frames



# 実際にQRコードを生成し、画像を組み合わせるための関数
# QRコード生成にはqrcodeモジュールを使用しています。画像の色調整、サイズ変更、ピクセル処理などが行う
def produce_impl(txt,img,ver=5,err_crt = qrcode.constants.ERROR_CORRECT_H,bri = 1.0, cont = 1.0,\
        colourful = False, rgba = (0,0,0,255),pixelate = False):
    """Produce QR code

    :txt: QR text
    :img: Image object
    :ver: QR version
    :err_crt: QR error correct
    :bri: Brightness enhance
    :cont: Contrast enhance
    :colourful: If colourful mode
    :rgba: color to replace black
    :pixelate: pixelate
    :returns: Produced image

    """
    # QRコードを生成
    qr = qrcode.QRCode(version = ver,error_correction = err_crt,box_size=3)
    qr.add_data(txt)
    qr.make(fit=True)

    # QRコードのイメージをRGBA形式に変換
    img_qr = qr.make_image().convert('RGBA')

    # カラフルモードが有効で、かつ置き換え色が黒でない場合、指定された色で黒を置き換え
    if colourful and ( rgba != (0,0,0,255) ):
        color_replace(img_qr,rgba)
    # 元の画像をRGBA形式に変換
    img_img = img.convert('RGBA')
    img_img_size = None
    # QRコードのサイズから24ピクセル引いた値をimg_sizeとして定義
    img_size = img_qr.size[0] - 24

    # img_imgの幅が高さより小さい場合img_img_sizeに幅を、そうでない場合は高さを代入
    if img_img.size[0] < img_img.size[1]:
        img_img_size = img_img.size[0]
    else:
        img_img_size = img_img.size[1]

    # img_imgを指定したサイズにクロップ
    #img_enh = img_img.crop((0,0,img_img_size,img_img_size))
    # img_imgを指定したサイズにクロップ
    img_enh = img_img
    # 画像のコントラストを強調
    enh = ImageEnhance.Contrast(img_enh)
    img_enh = enh.enhance(cont)

    # 画像の明るさを強調
    enh = ImageEnhance.Brightness(img_enh)
    img_enh = enh.enhance(bri)

    # カラフルモードが無効なら、ピクセル化が有効なら1bitモードに変換し、RGBA形式に変換
    if not colourful:
        if pixelate:
            img_enh = img_enh.convert('1').convert('RGBA')
        else:
            img_enh = img_enh.convert('L').convert('RGBA')
    img_frame = img_qr
    # img_enhを拡大縮小
    img_enh = img_enh.resize((img_size*10,img_size*10), Image.NEAREST)
    # L形式に変換されたimg_enhを指定サイズに変換
    img_enh_l = img_enh.convert("L").resize((img_size,img_size), Image.NEAREST)
    # img_frame_lはL形式に変換されたimg_frame
    img_frame_l = img_frame.convert("L")

    # 一部のピクセルを透明にする処理
    for x in range(0,img_size):
        for y in range(0,img_size):
            if x < 24 and (y < 24 or y > img_size-25):
                continue
            if x > img_size-25 and (y < 24 ):
                continue
            if (x%3 ==1 and  y%3 == 1):
                if (img_frame_l.getpixel((x+12,y+12)) > 70 and img_enh_l.getpixel((x,y)) < 185)\
                        or (img_frame_l.getpixel((x+12,y+12)) < 185 and img_enh_l.getpixel((x,y)) > 70) :
                    continue
            img_frame.putpixel((x+12,y+12),(0,0,0,0))
    # QRコードのパターン位置を取得
    pos = qrcode.util.pattern_position(qr.version)

    # QRコードのイメージを再度生成し、RGBA形式に変換
    img_qr2 = qr.make_image().convert("RGBA")

    # カラフルモードが有効で、かつ置き換え色が透明でない場合、指定された色で黒を置き換え
    if colourful and ( rgba != (0,0,0,0) ):
        color_replace(img_qr2,rgba)

    # パターン位置を基に一部の領域を切り取り、img_tmpに貼り付け
    for i in pos:
        for j in pos:
            if (i == 6 and j == pos[-1]) or (j == 6 and i == pos[-1])\
                or (i == 6 and j == 6):
                continue
            else:
                rect = (3*(i-2)+12,3*(j-2)+12,3*(i+3)+12,3*(j+3)+12)
                img_tmp = img_qr2.crop(rect)
                img_frame.paste(img_tmp,rect)
    scale_factor = 20  # 調整したい拡大縮小倍率
    # 新しいRGBA形式のイメージを作成
    img_res = Image.new("RGBA",(img_frame.size[0]*10,img_frame.size[1]*10),(255,255,255,255))
    # img_enhを指定位置に貼り付けます
    img_res.paste(img_enh,(120,120),img_enh)
    # img_frameを拡大縮小します
    img_frame = img_frame.resize((img_frame.size[0]*10,img_frame.size[1]*10), Image.NEAREST)
    # img_frameを新しいイメージに貼り付けます
    img_res.paste(img_frame,(0,0),img_frame)
    # img_resをRGB形式に変換します
    img_res = img_res.convert('RGB')

    # pixelateが有効なら、一度img_qrのサイズにリサイズし、その後元の画像サイズに再度リサイズ
    if pixelate:
        return img_res.resize(img_qr.size, Image.NEAREST).resize((img_img_size,img_img_size), Image.NEAREST)
    return img_res

def pre(URLTEXT,SRC_IMAGE_PATH, main_image_path,preview_image_path):
    import pyshorteners

    def frames_to_gif(frames, output_path, duration=10, loop=0):
        frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=duration, loop=loop, optimize=True)
    #def frames_to_gif(frames, output_path, duration=100, loop=0):
    #    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=duration, loop=loop, optimize=True, duration=duration)


        

    try:
        
        if len(URLTEXT) > 58:
            shortener=pyshorteners.Shortener()
            shorted_link=shortener.tinyurl.short(URLTEXT)
            URLTEXT = shorted_link

        URL = URLTEXT
        src = str(SRC_IMAGE_PATH)

        frames = produce(URL, src, ver=1, err_crt=qrcode.constants.ERROR_CORRECT_H, bri=1.0, cont=1.0,
                    colourful=True, rgba=(0,0,0,255), pixelate=False)
        
        
        frames[0].save(main_image_path)
        frames[0].save(preview_image_path)
        # #画像
        # if len(frames) == 1 or 'output.png'.upper()[-3:] != "GIF":
        #     frames[0].save(main_image_path)
        #     frames[0].save(preview_image_path)
        #     print("2")

        # # GIF
        # elif len(frames) == 1 or 'output.gif'.upper()[-3:] != "GIF":
        #     frames[0].save('output2.gif', loop=0)
        #     print("3")

        # if len(frames) > 1:
        #     frames_to_gif(frames, 'output3.gif', duration=100, loop=0)
        #     print("4")

    except Exception as e:
        print("エラーが発生しました:", e)

