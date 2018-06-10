# bnb-Cal.py # v2.5  2018/6/8
# 各物件の予約状況および料金の取得 ライブラリーモジュール
# seleniumを使う

# 2018-5-25、6-4
# 2018/6/8 v2.5 最低泊数を各可能日より取得

import sys
from datetime import date, datetime, timedelta
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

#import requests


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
    #print('入力ファイル: ' + fname)
                    
    return list_of_blocks

def fromstrtodate(t):
    return date(int(t[:4]), int(t[4:6]), int(t[6:8]))

        
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

class bnbCalender:
    """ Calender of One Listing of AirBnb """
    dd=date.today()
    y=dd.year
    m=dd.month
    d=dd.day
    one_day=timedelta(days=1)
    
    def __init__(self, driver, listing_id):
       
        self.id = listing_id
        self.driver = driver
        #self.driver.implicitly_wait(20)
        self.uri = 'https://www.airbnb.jp/rooms/' + listing_id + '?s=OByL9hD4'
        self.driver.get(self.uri)
        
        self.monthday=month_day(self.y,self.m)#今月の日数
        self.view_month=date.today().month
        #祝日ファイル
        blocks_in = file_split('bnb_Cal_holiday.txt')
        self.holidays=[]
        for tex in blocks_in[1]:
            d=fromstrtodate(tex[:8])
            self.holidays.append(d)

        #print (self.holidays)
        
    def main_check(self):
        sleep(2)
        cl= self.driver.find_element_by_tag_name('main').get_attribute('class')
        if cl=='_e296pg':
            return True
        else:
            return False
        
    def minstay_g(self):
        """ 最低泊数 """
        actions = ActionChains(self.driver)
        for ind in range(1):
            actions.send_keys(u'\ue00f').perform()#PAGE_DOWN
        try:
            elm = self.driver.find_elements_by_xpath("//div[@class='_q401y8m']")
            staytext=elm[0].find_elements_by_tag_name("span")[1].text
            print(staytext)
           
        except:
            print('最低泊数取得失敗　id=', self.id )
            self.min_stay_g=0
        if staytext[:2]=='最低':
            self.min_stay_g= int(staytext[2:-1])
        else:
            self.min_stay_g=0
            
        self.min_stay=self.min_stay_g
        return self.min_stay_g

    def month_check(self):
        
        try:
            elm= self.driver.find_elements_by_xpath("//div[@Class='_gucugi']")[1]
            print(' ')
            print('カレンダー= ', elm.find_elements_by_tag_name('strong')[0].text)
            return True
        except:
            return False
               

    def calender_shift(self):
        try:
            self.driver.find_elements_by_xpath("//button[@Class='_121ogl43']")[0].click()
            #print(el_shift.get_attribute('aria-label') )
            sleep(4)
            self.month_check() 
            return True
        except:
            print('カレンダー移行失敗　id=', self.id, ' 月=', self.view_month)
            return False
        
    def td_shift(self, d):
        """その月のカレンダーが始まる位置。　左端（日曜）を-1とする"""
        w_day = date(d.year, d.month, 1).weekday()
        if w_day == 6:
            return -1
        else:
            return w_day
        
    
    def get_calendar2(self, d):
        """表示されている2月分のカレンダー情報を2重リストに納める"""
        self.calenders = []#月リスト
        self.tabs = self.driver.find_elements_by_xpath("//table[@Class='_p5jgym']")
        for ind in range(2):
            td_shift= self.td_shift( date(d.year, d.month, 1) + ind*self.one_day*31 )
            #この月のすべての日を表すtdを取得する（日リスト）
            self.calenderdays=self.tabs[ind+1].find_elements_by_tag_name("td")
            #上記tdから、1日より前の、空のtdを除いて、月リストに加える
            self.calenders.append(self.calenderdays[td_shift+1:])
        
    def is_followed(self, d, minst):
        """最低泊数分が空いているかチェックする"""
        #minst=self.minstay()
        flag=1
        
        for ind in range(minst-1):
            #
            next_day = d + self.one_day*(ind+1)
            if next_day.month < d.month:
                #チェックアウト月がチェックイン月より小さくなるのは、次の月（1月）だから
                mon_index = 1
            else:
                mon_index = next_day.month - d.month #同月であれば0,次の月であれば1
                
            day_index = next_day.day -1
            
            if self.calenders[mon_index][day_index].get_attribute('class') == '_12fun97':
                pass
            else:
                flag=0
                break
        return flag
    
    def check_minstay(self):
        actions = ActionChains(self.driver)
        #チェックイン日をクリックする
        check_in= self.calenders[0][self.check_date.day-1]
        check_in.click()
        print('checking minimum stay at: ', self.check_date )
        sleep(1)
        #最低泊数を確認する     
        try:
            count=0
            while count<4:
                count=count+1
                elm= self.driver.find_elements_by_xpath("//div[@class='_q401y8m']")
                staytext=elm[0].find_elements_by_tag_name("span")[1].text
                print(staytext)
                if staytext[:6]=='最低宿泊日数':
                    count=4
                else:
                    sleep(1)                    
                    actions.send_keys(u'\ue00f').perform()#PAGE_DOWN
                    sleep(1)
                    #チェックイン日をクリックする
                    #check_in= self.calenders[0][self.check_date.day-1]
                    check_in.click()
        except:
            print('最低泊数取得失敗 ')
            staytext=''
            
        if staytext != '':
            try:
                self.min_stay=int(staytext[6:-1])
                print('最低泊数: ',staytext[6:-1])
            except:
                print('最低泊数解釈失敗 ')
                self.min_stay=1
                #最低泊数 不明の場合は1日とする
        else:
            self.min_stay=1
            
        #「日付を消去」をクリック
        try:
            elm=self.driver.find_element_by_xpath("//div[@class='_79dbpfm']")
            elm.find_element_by_tag_name("button").click()
            #print('button _b82bweu: ', len(elms))
            sleep(1)
        except:
            pass
        
    def reserve(self):
        """チェックイン日、チェックアウト日をクリックする"""
        #sleep(1)
        #self.driver.find_element_by_xpath("//input[@id='checkin']").send_keys(u'\ue007')#enter
        #チェックイン日をクリックする
        check_in= self.calenders[0][self.check_date.day-1]
        check_in.click()
        print('check in = ', self.check_date)
        #self.driver.find_element_by_xpath("//input[@id='checkout']").send_keys(u'\ue007')
        
        #チェックアウト日を計算する        
        checkout=self.check_date + self.min_stay*self.one_day        
            
        if checkout.month < self.check_date.month:
            #チェックアウト月がチェックイン月より小さくなるのは、次の月（1月）だから
            mon_index = 1
        else:
            mon_index = checkout.month - self.check_date.month #同月であれば0,次の月であれば1
        day_index = checkout.day -1        
        #チェックアウト日をクリックする
        sleep(1)
        self.calenders[mon_index][day_index].click()
        #sleep(1)
        
    def get_def_price(self):
        try:
            charge_div=self.driver.find_element_by_xpath("//div[@class='_16tcko6']")
            spans=charge_div.find_elements_by_tag_name('span')
            return(remove_comma(spans[3].text[2:]))
        except:
            return '0'
        
    def get_charge(self,rwait,rlimit):
        actions = ActionChains(self.driver)
        #sleep(1)
        charges=[]
        #料金のdiv
        charge_div=self.driver.find_element_by_xpath("//form[@id='book_it_form']")
        get_flag=False
        itr=0
        while get_flag==False and itr<rlimit:
            itr=itr+1
            try:
                spans=charge_div.find_elements_by_xpath("//span[@class='_j1kt73']")
                if len(spans)>1:
                    get_flag=True
                    for sp in spans:
                        t=sp.text[2:]
                        #print(int(remove_comma(t)))
                        charges.append(remove_comma(t))
                    if len(charges)==2:
                        charges.insert(1,'0')#service fee
                    if len(charges)==3:
                        charges.insert(1,'0')#cleaning fee
                else:
                    #get_flag=False                    
                    actions.send_keys(u'\ue00f').perform()#PAGE_DOWN
                    self.reserve()
                    sleep(rwait)
            except:
                actions.send_keys(u'\ue00f').perform()#PAGE_DOWN
                self.reserve()
                sleep(rwait)
                
        #「日付を消去」をクリック
        try:
            elm=self.driver.find_element_by_xpath("//div[@class='_79dbpfm']")
            elm.find_element_by_tag_name("button").click()
            #print('button _b82bweu: ', len(elms))
            sleep(1)
        except:
            pass
            
        return charges
        
    def get_pos(self):
        """ページをスクロールダウンして地図を表示させ、緯度経度を取得する"""
        elm=self.driver.find_element_by_xpath("//div[@Class='_1fmyluo4']")
        
        actions = ActionChains(self.driver)
        for ind in range(5):
            actions.send_keys(u'\ue00f').perform()#PAGE_DOWN
            
        elms2=elm.find_elements_by_tag_name('a')
        #print(len(elms2))
        h = elms2[0].get_attribute('href')
        pos_texts = h.split('=')[1].split(',')
        longitude = pos_texts[0]#緯度
        latitude = pos_texts[1][:-2]#経度
        #print('緯度= ', longitude)
        #print('経度= ', latitude)
        return (longitude,latitude)
    
        
    def find_av_day(self, target_date):
        """予約可能日かどうかチェックし、可能なら予約操作を行う"""
        
        self.check_date = target_date
        self.get_calendar2(self.check_date)
        
        #self.check_date = self.check_date + self.one_day
        #uptod = self.dd+ one_day*30
        
                    
        #月が変わったか
        if self.check_date.month != self.view_month:
                
            #カレンダー表をシフトし、td のインデックスを変更
            f=self.calender_shift()
            self.view_month = self.check_date.month #  12-to-1も考慮
            #td_shift= self.td_shift( self.check_date )
            self.get_calendar2(self.check_date)
                
        td_index=self.check_date.day-1
        #予約可能日か
        if self.calenders[0][td_index].get_attribute('class') == '_12fun97':
            #
            if self.min_stay_g==0:
                self.check_minstay()
            
            if self.min_stay == 1:
                self.reserve()#予約操作に進む
                return 'A'
                    
            else:   
                #連泊可能か                
                if self.is_followed(self.check_date, self.min_stay) == 1:
                    self.reserve()#予約操作に進む
                    return 'A'
                else:
                    return 'F'
                        
        else:         
            return 'N'
        
    def is_holiday(self, t):
        if t in self.holidays:
            return 'H'
        else:
            return 'N'
        
            
#Main
if __name__ == "__main__":
    '''
    t='180605'
    print(int(t[2:4]))
    d=date(int('20'+t[:2]), int(t[2:4]), int(t[-2:]))
    print(d)
    #pass
    '''
    blocks_in = file_split('bnb_Cal_holiday.txt')
    holidays=[]
    for tex in blocks_in[1]:
        d=datetime.strptime(tex[:8],'%Y%m%d')
        holidays.append(d)

    print (holidays)


    if date(2018, 11, 3) in holidays:
        print('H')
    else:
        print('N')
