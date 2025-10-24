
import flask_excel as excel
import re
from mimetypes import guess_type
from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
from flask_session import Session
from otp import genotp
from cmail import send_email
from stoken import generate_token, verify_token
import mysql.connector
from io import BytesIO
mydb=mysql.connector.connect(user='root',password='121212@',host='localhost',database='snmdb')
app=Flask(__name__)
excel.init_excel(app)
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key='privatekey123'
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username=request.form['username']
        usermail=request.form['usermail']
        password=request.form['password']   
        cursor=mydb.cursor(buffered=True)   
        cursor.execute("select count(*) from user where usermail=%s",[usermail])
        count_mail=cursor.fetchone()
        if count_mail[0]==1:
            flash('Usermail already registered. Please use a different email.')
            return redirect(url_for('register'))
        else:
            gotp=genotp() #server otp
            userdata={'username':username,'usermail':usermail,'password':password,'otp':gotp}
            subject="Your OTP Code"
            body=f"Hello {username},\n\nYour OTP code is: {gotp}\n\nThank you!"
            send_email(to=usermail, subject=subject, body=body)
            flash('OTP has been sent to your email address. Please verify.')
            return redirect(url_for('otpverify', udata=generate_token(data=userdata)))
    return render_template('register.html')
@app.route('/otpverify/<udata>',methods=['GET','POST'])
def otpverify(udata):
    if not session.get('user'):
        flash('Please login first')
        return redirect(url_for('userlogin'))
    else:
        if request.method == 'POST':
            user_otp=request.form['otp']
            de_userotp = verify_token(udata)
            if de_userotp['otp'] == user_otp:
                cursor=mydb.cursor(buffered=True)
                cursor.execute("INSERT INTO user (username, usermail, password) VALUES (%s, %s, %s)",[de_userotp['username'],de_userotp['usermail'],de_userotp['password']])
                mydb.commit()
                cursor.close()
                flash(f'Successfully Registered {de_userotp["username"]}')
                return redirect(url_for('login.html'))

            else:
                flash('Invalid OTP. Please try again.')
                return redirect(url_for('otpverify', udata=udata))
    return render_template('verify.html')
@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if not session.get('user'):
        if request.method == 'POST':
            login_usermail=request.form['usermail']
            login_password=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute("SELECT count(usermail) FROM user WHERE usermail=%s",[login_usermail])
            count_usermail=cursor.fetchone()
            print(count_usermail)
            if count_usermail[0]==1:
                cursor.execute("SELECT password FROM user WHERE usermail=%s",[login_usermail])
                stored_password=cursor.fetchone()
                if stored_password[0]==login_password:
                    session['user']=login_usermail

                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid Password')
                    return redirect(url_for('userlogin'))
            else:
                flash('Invalid Usermail')
                return redirect(url_for('userlogin'))
        return render_template('login.html')
    else:
        return redirect(url_for('dashboard'))
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('Logged out successfully')
        return redirect(url_for('userlogin'))
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))


@app.route('/addnotes', methods=['GET', 'POST'])
def addnotes():
    if not session.get('user'):
        flash('Please login first')
        return redirect(url_for('userlogin'))
    else:
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select userid from user where usermail=%s",[session.get('user')])
            user_id=cursor.fetchone()
            cursor.execute("insert into notesdata(title, description, added_by) values(%s,%s,%s)",[title,description,user_id[0]])
            mydb.commit()
            flash('Note added successfully!')
        return render_template('addnotes.html')
@app.route('/viewall_notes')
def viewall_notes():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select userid from user where usermail=%s",[session.get('user')])
        user_id=cursor.fetchone()
        cursor.execute("select notesid,title,description,created_at from notesdata where added_by=%s",[user_id[0]])
        stored_notes=cursor.fetchall()
        return render_template('viewall_notes.html',notes=stored_notes)
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/view_notes/<nid>')
def view_notes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select * from notesdata where notesid=%s",[nid])
        note=cursor.fetchone()
        return render_template('view_notes.html',note=note)
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/delete_notes/<nid>')
def delete_notes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("delete from notesdata where notesid=%s",[nid])
        mydb.commit()
        cursor.close()
        flash('Note deleted successfully!')
        return redirect(url_for('viewall_notes'))
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/update_notes/<nid>', methods=['GET', 'POST'])
def update_notes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select * from notesdata where notesid=%s",[nid])
        note=cursor.fetchone()
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute("update notesdata set title=%s, description=%s where notesid=%s",[title,description,nid])
            mydb.commit()
            cursor.close()
            flash('Note updated successfully!')
            return redirect(url_for('view_notes',nid=nid))
        return render_template('update_notes.html',note=note)
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/fileupload', methods=['GET', 'POST'])
def fileupload():
    if session.get('user'):
        if request.method == 'POST':
            filedata = request.files['file']
            fname = filedata.filename
            fdata=filedata.read()
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select userid from user where usermail=%s",[session.get('user')])
            user_id=cursor.fetchone()
            cursor.execute("insert into file_data(filename, filedata,added_by) values(%s,%s,%s)",[fname,fdata,user_id[0]])
            mydb.commit()
            cursor.close()
            flash('File uploaded successfully!')
        return render_template('fileupload.html')
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/viewall_files')
def viewall_files():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select userid from user where usermail=%s",[session.get('user')])
        user_id=cursor.fetchone()
        cursor.execute("select fid,filename,created_at from file_data where added_by=%s",[user_id[0]])
        stored_files=cursor.fetchall()
        return render_template('view_allfiles.html',files=stored_files)
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/view_file/<fid>')
def view_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select * from file_data where fid=%s",[fid])
        fdata=cursor.fetchone()
        array_data=BytesIO(fdata[2])
        mine_type,_=guess_type(fdata[1])
        return send_file(array_data,as_attachment=False,download_name=fdata[1],mimetype=mine_type or 'application/octet-stream')
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/download_file/<fid>')
def download_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select * from file_data where fid=%s",[fid])
        fdata=cursor.fetchone()
        array_data=BytesIO(fdata[2])
        mine_type,_=guess_type(fdata[1])
        return send_file(array_data,as_attachment=True,download_name=fdata[1],mimetype=mine_type or 'application/octet-stream')
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/delete_file/<fid>')
def delete_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("delete from file_data where fid=%s",[fid])
        mydb.commit()
        cursor.close()
        flash('File deleted successfully!')
        return redirect(url_for('viewall_files'))
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select userid from user where usermail=%s",[session.get('user')])
        user_id=cursor.fetchone()
        cursor.execute("select notesid,title,description,created_at from notesdata where added_by=%s",[user_id[0]])
        userdata=cursor.fetchall()
        hedings=['Notes ID','Title','Description','Created At']
        array=[list(i) for i in userdata]
        array.insert(0,hedings)
        return excel.make_response_from_array(array,"xlsx",file_name="notesdata")
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/search', methods=['GET','POST'])
def search():
    if session.get('user'):
        usersearch=request.form['search']
        strg=['A-Za-z0-9']
        pattern=re.compile(f'^{strg}',re.IGNORECASE)
        if pattern.match(usersearch):
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select userid from user where usermail=%s",[session.get('user')])
            user_id=cursor.fetchone()
            cursor.execute("select notesid,title,description,created_at from notesdata where notesid like %s OR title LIKE %s OR description LIKE %s or created_at LIKE %s and added_by=%s",[usersearch+'%',usersearch+'%',usersearch+'%',usersearch+'%',user_id[0]])
            resultsearch=cursor.fetchall()
            cursor.execute('select fid,filename,created_at from file_data where fid like %s or filename like %s or created_at like %s and added_by=%s',[usersearch+'%',usersearch+'%',usersearch+'%',user_id[0]])
            resultfiles=cursor.fetchall()
            return render_template('dashboard.html',resultsearch=resultsearch,resultfiles=resultfiles)
        else:
            flash('Invalid search input')
            return render_template('dashboard.html')
    else:
        flash('Please login first')
        return redirect(url_for('userlogin'))
@app.route('/forgotpassword', methods=['GET','POST'])
def forgotpassword():
    if request.method == 'POST':
        user_mail=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select count(*) from user where usermail=%s",[user_mail])
        count_mail=cursor.fetchone()
        if count_mail[0]==1:
            subject="reset link for password update simple notes management system"
            body=f"use the given link to reset your password {url_for('resetpassword',udata=generate_token(data=user_mail), _external=True)}"
            send_email(to=user_mail, subject=subject, body=body)
            flash('Password reset link has been sent to your email.')
            return redirect(url_for('userlogin'))
        else:
            flash('Email not registered. Please check and try again.')
            return redirect(url_for('register'))
    return render_template('forgotpassword.html')
@app.route('/resetpassword/<udata>', methods=['GET','PUT'])
def resetpassword(udata):
    if request.method == 'PUT':
        new_password=request.get_json('password')['password']
        de_udata=verify_token(udata)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('update user set password=%s where usermail=%s',[new_password,de_udata])
        mydb.commit()
        cursor.close()
        flash('Password updated successfully. Please login.')
        return "ok"
    return render_template('npassword.html',udata=udata)
if __name__=='__main__':
    app.run(debug=True,use_reloader=True)
