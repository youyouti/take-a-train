#coding: UTF-8

# pyMySQL のサブクラス
# worked from 2018.5.22
# completed 2018.5.
# 


import pymysql.cursors


def strip(tex):
    s=0
    while tex[s]==' ' or tex[s]=='\t':
        s =s +1
    e=-1
    while tex[e]==' ' or tex[e]=='\t' or tex[e]=='\n' or tex[e]=='\r':
        e = e -1
    if e==-1:
        return tex[s:]
    else:
        return tex[s:e+1]



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

class doMySQL:
    """MySQL へのデータアクセス"""
    
    def __init__(self, fil):
        #設定ファイル
        self.blocks_in = file_split(fil)
        headers= self.blocks_in[0]
        host=headers[0].split('=')[1][:-1]
        #print(host)
        user=headers[1].split('=')[1][:-1]
        #print(user)
        pw=headers[2].split('=')[1][:-1]
        #print(pw)
        db=headers[3].split('=')[1][:-1]
        print('database= ', db, '\n')

        self.conn = pymysql.connect(host=host,
                             user=user,
                             password=pw,
                             db=db,
                             charset='utf8',
                             local_infile=True,
                             # Selectの結果をdictionary形式で受け取る
                             cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.conn.cursor()
        
        
    def b_num(self):
        
        return(len(self.blocks_in))

    def create_table(self, ind):
        """initファイルの第indブロックに記述されたテーブルを新規作成する"""
        #indは0から始まる
        self.columns= self.blocks_in[ind]
        
        #新規テーブルを作成        
        tab_name = strip(self.columns[0].split('\t')[1] )
        self.create_table_cont(tab_name)
        
    def create_table_vn(self, tab_name, ind):
        """テーブル名を指定して新規作成する"""
        self.columns= self.blocks_in[ind]
        self.create_table_cont(tab_name)
                               
    def create_table_cont(self, tab_name):
        """テーブルを新規作成する の続き"""
        self.column_names = []                       
        print (tab_name)
        sql = "create table if not exists " + tab_name + ' ('
        for lin in range(1, len(self.columns)):
            words= self.columns[lin].split('\t')
            cname= strip(words[1])
            ctype= strip(words[2])
            self.column_names.append(cname)
            if ctype == 'varchar' or ctype == 'char':                
                sentence= cname + ' ' + ctype + '(' \
                     + strip(words[3]) + '), ' #カラム物理名, type,length
            else:
                sentence= cname + ' ' + ctype + ',' #カラム物理名, type
                
            print(sentence)
            sql = sql + sentence
            if lin==1 :
                prima = cname
                
        sentence = ' PRIMARY KEY(' + prima + '))'
        sql = sql + sentence
        print('\nsql= ',sql,'\n')
        try:
            self.cursor.execute(sql)
        except:
            pass
        
    def show_tables(self):
        
        sql='show tables'
        self.cursor.execute(sql)

        
    def exe(self, sql):
        
        self.cursor.execute(sql)
        
    def load_data(self, fil, table, separater, columns=[] ):
        """テキストファイルから一括書き込み"""

        if len(columns)==0:
            columns=self.column_names
            
        sql= "LOAD DATA LOCAL INFILE '"+ fil+ "' INTO TABLE " + table + " ( "             
            
        for column_name in columns:
            sql = sql + column_name + ','            
        sql=sql[:-1] + ")" #+ " FIELDS TERMINATED BY '"+ separater + "' LINES TERMINATED BY '\r\n'"
        #print (sql)
        print ('\n SQLに書き込み\n')
        self.cursor.execute(sql)
        self.conn.commit()

    def fetch_many(self, num):
        return (self.cursor.fetchmany(num))
                
    def display_all(self):
        
        dbdata = self.cursor.fetchall()
        for rows in dbdata:
            print(rows)
            
    def drop(self, ind):
        
        data= self.blocks_in[ind+1]
        tab_name = strip(data[0].split('\t')[1] )
        sql ="drop table " + tab_name
        print(sql)  
        self.cursor.execute(sql)
        
    def close(self):
        self.conn.close()

        
# main                
if __name__ == "__main__":

    print("PyMySQL Create Tables\n")

    #dt = datetime.now()

    db = doMySQL('py15-2.1-table_def.txt')
    db.create_table(0)
    
    #print('data_block=', db.b_num())

    #db.show_tables()
    '''
    for ind in range( db.b_num()-1 ):
        db.create_table(ind)

    #test
    
            #データを書き入れ
    sql ="INSERT INTO calender_test_01 (property_id, availability) VALUES('100','1')"
    db.exe(sql)
    
            #表示する
    sql = "SELECT * FROM calender_test_01"
    db.exe(sql)

    db.display_all()
    
    '''
    #db.close()

     
    print("\ndone!\n")





