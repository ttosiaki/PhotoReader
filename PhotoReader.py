#!/usr/bin/python3
# coding: utf-8

#////////////////////////////////////////////////////////////////////////////#
#   Photo Reader                                                             #
# ----------------                                                           #
#                                                                            #
# Date:      Ver   Auther                                                    #
# 2020/ 4/28 0.8   T.Toshiaki  Initial release                               #
#////////////////////////////////////////////////////////////////////////////#
import tkinter as Tk
from tkinter import filedialog as tkFileDialog #python3
import os
import shutil
import glob
import datetime
import json
from PIL import Image
from PIL.ExifTags import TAGS

#-----------------------------------------------------------------------
#   Widget Text                                                         
# ---------------
#
#-----------------------------------------------------------------------
class WidgetText:

    ###------------------#
    ##  Constructor     ##
    #------------------###
    def __init__( self, frame ):

        self.widget = Tk.Text( frame )
        self.widget.pack( side='top' )

    ###------------------#
    ##  Put message     ##
    #------------------###        
    def put( self, message ):
        
        self.widget.insert(Tk.END, message)
        self.widget.see( Tk.END )
        
#-----------------------------------------------------------------------
#   Widget DCIM Selector                                                
# ------------------------
#
#-----------------------------------------------------------------------
class WidgetDcimSelect:

    ###------------------#
    ##  Constructor     ##
    #------------------###
    def __init__( self, frame ):

        self.wdgEnt = Tk.Entry( frame )
        self.wdgEnt.pack( side='top' )
    
        self.wdgBtn = Tk.Button( frame, text="Select", command=self.readDcim )
        self.wdgBtn.pack( side='top' )

        self.wdgBtnStart= Tk.Button( frame, text="START", command=self.startBackup)
        self.wdgBtnStart.pack( side='top' )
        
    
    def readDcim( self ):
        # dcimMan.readFiles( "/home/tosiaki/PhotoReader/DCIM/100SHARP/" )
        filetypes = [('DCIM folder','*')] 
        dcim_path = tkFileDialog.askdirectory(initialdir="c:\\")

        ## Dcim Manにパスを渡す
        #
        ret = dcimMan.setPath( dcim_path )

        if (ret != True):
            wdgText.put( dcim_path )
            wdgText.put( " は、DCIMフォルダではありません。\n" )
    
    ###-----------------------------------------#
    ##  Start Backup / Backup処理をキック       ##
    #-----------------------------------------###
    def startBackup( self ):

        backupMan.start()

#-----------------------------------------------------------------------
#   Config Manager 
# ----------------------
# 設定ファイル (photobackup.cfg) を読みだして情報を保持する。
#
#-----------------------------------------------------------------------
class ConfigManager:
    
    ###---------------#
    ##  Setup        ##
    #---------------###
    def setup( self ):
       
        with open( "photoreader.cfg" ) as fd:
            json_data = json.load(fd)

        self.backup_path = json_data['BackupPath'] + "/"
        self.ketai_names = json_data['KetaiNames']
        
        ## Backup先フォルダのチェック
        #
        if (os.path.isdir( self.backup_path ) == True):
            wdgText.put( "バックアップ・フォルダ:\n" )
            wdgText.put( self.backup_path + "\n\n" )
        else:
            wdgText.put( "このバックアップ・フォルダはありません。\n" )
            wdgText.put( self.backup_path + "\n\n" )
            self.backup_path = ""

    ###-----------------------------------------------------------------#
    ##  Check Ketai mode / 渡された DCIMフォルダ名がリストにあるか調べる  ##
    #-----------------------------------------------------------------###
    def checkKetai( self, dir_name ):

        ## ketai_namesリストを検索
        #
        for n in self.ketai_names:
            if (dir_name == n):
                return True
        ## 見つからなければ Falseを返す
        return False
                
#-----------------------------------------------------------------------
#   Backup Manager 
# ------------------
#                                                                          
# ketai_mode - スマホ/携帯電話など MCTPデバイスの場合、フォルダ名が入る
#              その場合、MCTPデバイス特有の処理を行う
#              
#-----------------------------------------------------------------------
class BackupManager:
    
    ###--------------------------#
    ##  Start photo backup      ##
    #--------------------------###            
    def start( self ):
        
        ## DCIMフォルダ配下の画像ファイルの一覧を取得
        #
        st = dcimMan.readFiles()
        if (st == False):
            wdgText.put( "This is not DCIM folder.\n" )
            return False
        
        ## Backupの前準備
        #
        self.obj_ptr = 0
        self.backup_path = configMan.backup_path
        self.source_path = dcimMan.dcim_folder
        self.ketai_mode = dcimMan.ketai_mode

        ## 前回のBackup Listがあれば読み出す
        ## (ketai_modeでなければ、Listは空のまま)
        ##
        next_backup_list = []
        last_backup_list = []
        if (self.ketai_mode != ""):
            backup_list_file = self.ketai_mode + ".lst"
            if (os.path.exists(backup_list_file) == True):
                with open( backup_list_file ) as fd:
                    last_backup_list = json.load(fd)

        ## DCIM Managerから 画像ファイルObjをもらってBackupする
        ## 画像ファイルが終わるまで繰り返す
        #
        obj = dcimMan.getFirstPhoto()
        while (obj):
            
            ## 前回Backup Listにある場合はスキップ
            ## (ketai_modeじゃなければListは空で常にCopy)
            fname = obj.file_name
            if (fname in last_backup_list) == True:
                wdgText.put( fname + " backuped already \n" )
                ret = True
            else:
                ## 画像ファイルをバックアップ
                ret = self.copy( obj )
            
            ## Copyが成功したら新Backup Listに追加
            if (ret == True):
                next_backup_list.append( fname )

            ## 次のObjを取り出す
            obj = dcimMan.getNextPhoto()

        ## 新Backup Listを保存
        #
        fp = open( self.ketai_mode+".lst", 'w' )
        json.dump( next_backup_list, fp )
        fp.close()
        
        wdgText.put( "Complete.\n" )
    
    ###---------------------------#
    ##  Copy photo file          ##
    #---------------------------###            
    def copy( self, obj ):

        ## Photo File Objから必要な情報を取り出す
        #
        fname = obj.file_name
        src_date = obj.shoot_date

        ## 撮影日をCopy先のフォルダ名に設定
        ## 撮影日情報がないものは、UnknownDate フォルダを使う
        #
        if (src_date == None):
            dst_dir = "UnknownDate"
        else:
            dst_dir = src_date.strftime('%Y_%m%d/')
        
        dst_path = self.backup_path + dst_dir
        ## フォルダがない場合は作成
        if (os.path.isdir( dst_path ) != True):
            os.mkdir( dst_path )
        
        wdgText.put( fname + " --> " + dst_dir + " " )

        ## コピー元先のパス名を設定
        #
        src_fpath = self.source_path + fname
        dst_fpath = dst_path + fname
            
        ## コピー前にファイルの重複がないか確認
        #
        if (os.path.isfile( dst_fpath ) == True):
            ## 同じファイル名がすでにコピーされてたら日付を比較
            ptime = os.path.getmtime( dst_fpath )
            dst_date = datetime.datetime.fromtimestamp( ptime )
            # dst_date = dst_ptime.strftime( '%Y_%m%d %H:%M%S' )
            # src_date = date.strftime( '%Y_%m%d %H:%M%S' )
            ## 日付も同じならコピー済

            print( fname )
            print( src_date )
            print( dst_date )
            if (src_date == dst_date):
                wdgText.put( "Copied \n" )
                return True
            else:
                # そうでなければ、別ファイルで名前が重複(Error終了)
                wdgText.put( "ファイル名重複 \n" )
                return False

        ## 画像ファイルをBackup先にコピー
        #
        shutil.copy( src_fpath, dst_path )
        
        ## ketai_modeの場合(MCTP)、ファイルに日付情報がないので、
        ## 撮影日時を Backupしたファイルの日付に設定する
        ## (日付情報がない場合はスキップ)
        #
        if (self.ketai_mode!="") & (src_date!=None):
            ptime = src_date.timestamp()
            os.utime( dst_path+fname, (ptime, ptime))

        wdgText.put( "OK \n" )
        
        return True

#-----------------------------------------------------------------------    
#   DCIM File Manager 
# ---------------------
#
# インスタンス変数：
# dcim_path   - Backup対象のDCIMフォルダまでのパス
# dcim_folder - DCIM/xxxx  DCIMの中のベンダ別のフォルダ名も含めたパス
#                                                                          
#-----------------------------------------------------------------------
class DcimFileManager:
    
    ###---------------#
    ##  Constructer  ##
    #---------------###
    def __init__( self ):
       
        # self.photo_list = []
        self.keitai_mode = False
        self.src_path = ""

    ###---------------#
    ##  Constructer  ##
    #---------------###
    def setPath( self, dcim_path ):
        
        ## DCIMフォルダであるかチェック
        #
        base_name = os.path.basename( dcim_path )
        if (base_name != "DCIM"):
            return False

        ## DCIMフォルダ内の１つ目のディレクトリを src_path とする
        # 
        dir_list = glob.glob( dcim_path + "/*" )
        self.dcim_folder = dir_list[0] + "/"
        
        wdgText.put( "ソースディレクトリ: " + self.dcim_folder + "\n" )
        
        ## 対象のフォルダが携帯電話(スマホ)かチェック
        ## (末尾に / があるとparseできないので、dir_list[0] を使う)
        #
        dir_name = os.path.basename( dir_list[0] )  
        if configMan.checkKetai( dir_name ) == True:
            wdgText.put( "ケータイモード: True \n" )
            self.ketai_mode = dir_name
        else:
            wdgText.put( "ケータイモード: False \n" )
            self.ketai_mode = ""

        return True
    
    ###-------------------------------------------------------#
    ##  Read Files / DCIMフォルダ内の画像ファイルの一覧を取得   ##
    #-------------------------------------------------------###
    def readFiles( self ):

        self.photo_list = {}

        ## DCIMディレクトリ内の画像ファイル一覧を作成
        ## (パス名は含まれない ファイル名のみ)
        #
        cwd = os.getcwd()               # カレントディレクトリを保存
        os.chdir( self.dcim_folder )
        file_list = glob.glob( "*" )
        os.chdir( cwd )                 # カレントディレクトリに戻す
        
        ## 画像ファイル毎にObjを生成
        #
        cnt = 0
        for fname in file_list:
            photo_obj = PhotoFile( self.dcim_folder + fname )
            self.photo_list[cnt] = photo_obj
            cnt = cnt +1
        
        self.obj_num = cnt

        str = '%d files read.\n' % cnt
        wdgText.put( str )
    
    ###----------------------#
    ##  Get First Photo     ##
    #----------------------###            
    def getFirstPhoto( self ):

        self.obj_ptr = 0
        return self.photo_list[ 0 ]

    ###----------------------#
    ##  Get Next Photo      ##
    #----------------------###            
    def getNextPhoto( self ):

        self.obj_ptr = self.obj_ptr +1
        if (self.obj_ptr == self.obj_num):
            return False
        
        return self.photo_list[ self.obj_ptr ]
    
#-----------------------------------------------------------------------
#   Photo File 
# --------------
#            
#  path - その画像のパスを含むファイル名
#  file_name  - 画像ファイルのファイル名
#  shoot_date - 撮影日時                                                
#-----------------------------------------------------------------------
class PhotoFile:
    
    ###---------------#
    ##  Constructer  ##
    #---------------###
    def __init__( self, path ):

        self.file_path = path
        self.file_name = os.path.basename( path )
        
        ## 画像ファイルからExifデータを取り出す
        #
        image_obj = Image.open( path )
        exif = image_obj._getexif()
        ## Exifデータが存在しない場合、shoot_date に None を設定して終了
        if (exif == None):
            self.shoot_date = None
            wdgText.put( self.file_name+" has no exif info \n" )
            return
        
        ## Exifデータを展開し、撮影日を取り出す
        #
        exif_info = {}
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            exif_info[tag] = value

        date = exif_info.get('DateTimeOriginal')
        ## 古いフォーマットの場合 'DateTime'タグを読みだす
        if (date == None):
            date = exif_info.get('DateTime')
        ## 撮影日時を dateitme型に変換
        if (date == None):
            self.shoot_date = None
            wdgText.put( self.file_name+" has no exif info \n" )
        else:
            self.shoot_date = datetime.datetime.strptime(date, '%Y:%m:%d %H:%M:%S' )
        
        return
    
    ###---------------#
    ##  Constructer  ##
    #---------------###
    def getName( self ):

        return( self.file_name )
    
    
class WidgetTest:

    def __init__( self, frame ):

        self.backup_list = []

        self.backup_list.append( "file1" )
        self.backup_list.append( "file2" )
        self.backup_list.append( "file3" )
        
        self.wdgBtn = Tk.Button( frame, text="TEST", command="" )
        self.wdgBtn.pack( side='top' )
        
    def putStatus( self, msg ):
        self.wgtEntry.delete( 0, Tk.END )
        self.wgtEntry.insert( Tk.END, msg )
    
    def test( self ):
        # dcimMan.readFiles( "/home/tosiaki/PhotoReader/DCIM/100SHARP/" )
        filetypes = [('DCIM folder','*')] 
        dcim_path = tkFileDialog.askdirectory(initialdir="c:\\")
        mainText.putStatus( dcim_path )
        dcimMan.dcim_path = dcim_path
    
    def backupPhotos( self ):
        backupMan.startBackup()

    def testBtn( self ):
        backupMan.test( "kyocera.lst" )

#-----------------------------------------------------------------------------
#   Main procedure
# ------------------
#
#-----------------------------------------------------------------------------

###-----------------------------#
##  Widgetの作成               ##
#-----------------------------###
frame = Tk.Tk()
frame.title( "Photo Reader" )

wdgText = WidgetText( frame )
wdgDcimSelect = WidgetDcimSelect( frame )

# wdgTest = WidgetTest( frame )

###-----------------------------#
##  主要な Objectの生成         ##
#-----------------------------###
dcimMan = DcimFileManager(  )
backupMan = BackupManager()
configMan = ConfigManager()
configMan.setup()

buff = Tk.StringVar()
buff.set('10')

frame.mainloop()
