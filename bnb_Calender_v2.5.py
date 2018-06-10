# bnb-Calender-v2.5.py # v2.5  2018/6/8
# 各物件の予約状況および料金の取得 main
# selenium を使う

# 2018.5.25, 6.3
# 2018/6/8 v2.5 最低泊数を各可能日より取得
import sys
from os import path
from datetime import date, datetime, timedelta
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

#import requests
#import pymysql.cursors
import pydoSQL
import bnb_Cal #1個のListing を調査するClass


def file_split(fname):
    """入力ファイルを開き、空白行でブロックに分割する"""
    fil = open(fname , encoding = 'utf-8')
    lines = fil.readlines()
    fil.close()
    lines[0] = lines[0][1:]
    
    list_of_blocks = []
    begin = 0
    ind = 0
    for line in lines:
        if line == '\n':
            if ind > begin:
                list_of_blocks.append(lines[begin:ind])
            begin = ind + 1
        ind = ind + 1
    if ind > begin:
        list_of_blocks.append(lines[begin:ind])
    
    #確認表示
    print('入力ファイル: ' + fname)
                    
    return list_of_blocks

        
def month_day(y,m):
        d1= datetime(y,m,1)
        if m==12:
            d2=datetime(y+1,1,1)
        else:            
            d2= datetime(y,m+1,1)
        return (d2-d1).days
    
def remove_comma(st):
    members=st.split(',')
    result=''
    for m in members:
        result=result + m
    return result
    #print(int(remove_comma('1,532')))

            
#Main
if __name__ == "__main__":

    print('\n  bnb-Calender-v2.5.py  2018-6-8\n')
    print ('start at: ',datetime.today(),'\n')
    
    init_data = file_split('bnb_Calender_init.txt')
    #exe_limit= int(init_data[2][1].split('\t')[-1])#終了ロット
    #print ('limit: ', exe_limit)
    lis_table= init_data[1][0].split('\t')[1]#入力（ListingのIDを集めた）テーブル名
    lis_tab_def= init_data[1][1].split('\t')[1]#入力テーブルの定義ファイル名
    out_tab_pre= init_data[1][3].split('\t')[1]#出力テーブル名のprefix
    out_tab_suf= init_data[1][4].split('\t')[1]#出力テーブル名のsufix
    out_tab_def= init_data[1][5].split('\t')[1]#出力テーブルの定義ファイル名
    temp_out_fil= init_data[1][6].split('\t')[1]#仮出力ファイル名
    period = int(init_data[1][7].split('\t')[1])#調査日数 

    retry_wait= int(init_data[2][0].split('\t')[1])#リトライ時間
    retry_count= int(init_data[2][1].split('\t')[1])#リトライ回数
    lotsize= int(init_data[2][2].split('\t')[1])#実行ロット（一度に処理する）内のListing 数
    startlot = int(init_data[2][3].split('\t')[1])#開始ロット
    endlot = int(init_data[2][4].split('\t')[1])#終了ロット
    
    #インプットSQL　= Listing ID
    sql_in= pydoSQL.doMySQL(lis_tab_def)    
    query = "SELECT property_id  FROM " + lis_table
    sql_in.exe(query)
    
    
    #アウトプットSQL
    sql_out= pydoSQL.doMySQL(out_tab_def)
    tab_name=out_tab_pre + date.today().strftime('%y%m%d')+out_tab_suf
    try:
        sql_out.create_table_vn(tab_name,1)
    except:
        pass
    
    
    #webdriverを起動
    driver = webdriver.Firefox()
    driver.implicitly_wait(20)

    for lot_count in range(startlot-1):
        listing_ids = sql_in.fetch_many(lotsize)

    lot_count=startlot-1
    d_len=lotsize
    while d_len == lotsize:
        lot_count=lot_count+1
        listing_ids = sql_in.fetch_many(lotsize)
        d_len = len(listing_ids)
        #fetchmany(10) のリターン
        #[{'property_id': '10031077'}, {'property_id': '10062534'}, {'property_id': '10296000'}, {'property_id': '10366183'}, {'property_id': '10481198'}, {'property_id': '10482707'}, {'property_id': '10482931'}, {'property_id': '10483899'}, {'property_id': '10484325'}, {'property_id': '10578179'}]
        print('\n next ',d_len)
        #仮出力ファイル
        print ('仮出力ファイル: ', temp_out_fil)
        fout = open( temp_out_fil, 'w')
        
        for lis_id_dict in listing_ids:
            
            #一つのlistingを開く
            print('\n id= ',lis_id_dict['property_id'])#' 'は自動的に外される
            #lis_count=lis_count+1
            
            lis = bnb_Cal.bnbCalender(driver, lis_id_dict['property_id'])
            sleep(1)
            
            #listingが削除されていないかチェック
            if lis.main_check()==True:
                #定価
                def_price=lis.get_def_price()
                print('定価 ',def_price)
                if def_price == '0':
                    print('Listing が利用できなくなっています: ',lis.id, '--定価が取得できない')
                else:    
                    #最低泊数    
                    minst=lis.minstay_g()
                    #print ('最低泊数',minst)
                    lis.month_check()
                    
                    target_date = date.today() + timedelta(days=1)#チェック開始日を明日とする
                    check_end_date = date.today() + timedelta(days=1)*period
                    
                    while target_date < check_end_date:
                        index = lis.id + '-' +target_date.strftime("%y%m%d")# as 10366183-180604
                        holiday = lis.is_holiday(target_date)
                        outline = index + '\t' + lis.id  + '\t' + target_date.strftime("%y%m%d") \
                                      + '\t' + '月火水木金土日'[target_date.weekday()] + '\t' + holiday 
                        #予約可能日かどうかチェックし、可能なら予約操作を行う                
                        is_avail = lis.find_av_day(target_date)
                        if is_avail == 'A':
                            outline = outline + '\tA'# availability
                            outline = outline + '\t' + str(lis.min_stay) #min_stay
                            outline = outline + '\t' + def_price
                            #料金
                            charges=lis.get_charge(retry_wait,retry_count)
                            print('料金',charges)
                            for fee in charges:
                                outline = outline + '\t' + fee

                        else:
                            if is_avail == 'F':
                                outline = outline + '\tF'# availability,当日空きだが連泊不能
                            else:
                                outline = outline + '\t_'# availability
                            outline = outline + '\t' + str(minst)#min_stay
                            outline = outline + '\t' + def_price + '\t_\t_\t_\t_'\
                                      
                        fout.write(outline + '\r\n')
                        target_date = target_date + timedelta(days=1)
                                
            else:
                print('Listing が利用できなくなっています: ',lis.id)
                
        fout.close()    
        sql_out.load_data(temp_out_fil, tab_name, '\t')
            
            
        if lot_count>=endlot:
            d_len=0
            
    sql_out.close() 
               
    sql_in.close()
    
    print ('end at: ', datetime.today(),'\n')
