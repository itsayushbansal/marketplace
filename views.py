import web,os,re,base64,json
import MySQLdb as mysql
from dbconfig import read_config


def connect_mysql():
    try:
        db_config = read_config(section='mysql')
        db = mysql.connect(**db_config)
        return db
    except:
        return None


urls = (
    '/', 'index'
)

allowed = (
    ('ayush', 'pass1'),
)

app = web.application(urls, globals())


class index:
    def GET(self):
        conn = connect_mysql()
        if not conn:
            return json.dumps({'status': 400, 'message': 'Some error occurred'})
        cursor = conn.cursor()
        query = "SELECT * from product WHERE is_deleted = 0"
        try:
            cursor.execute(query)
            columns = cursor.description
            result = []
            for value in cursor.fetchall():
                tmp = {}
                for (index, column) in enumerate(value):
                    tmp[columns[index][0]] = column
                result.append(tmp)
            conn.close()
            return json.dumps({'status': 200, 'data': result}, default=str)
        except:
            conn.close()
            return json.dumps({'status': 400, 'message': 'Some error occurred'})

    def POST(self):
        if not is_authenticated(self):
            return json.dumps({'status': 401, 'message': 'Invalid Authentication'})
        conn = connect_mysql()
        if not conn:
            return json.dumps({'status': 400, 'message': 'Some error occurred'})
        required = ['name', 'price', 'description', 'quantity']
        form_data = web.input()
        for key in required:
            if key not in form_data:
                return json.dumps({'status': 400, 'message': key + ' field is required'})
        cursor = conn.cursor()
        try:
            query = "INSERT INTO product(name,price,description,quantity) VALUES('%s','%s','%s','%s')" % (
                str(form_data.get('name')), float(form_data.get('price')), str(form_data.get('description')),
                int(form_data.get('quantity')))
            cursor.execute(query)
            conn.commit()
            conn.close()
            return json.dumps({'status': 200, 'message': 'Product Added Successfully'})
        except:
            conn.rollback()
            conn.close()
            return json.dumps({'status': 400, 'message': 'Some error occurred'})

    def PUT(self):
        if not is_authenticated(self):
            return json.dumps({'status': 401, 'message': 'Invalid Authentication'})
        conn = connect_mysql()
        if not conn:
            return json.dumps({'status': 400, 'message': 'Some error occurred'})
        required = ['product_id']
        update_fields = ['name', 'price', 'description', 'quantity', 'created_at', 'updated_at', 'image']
        form_data = web.input()
        product_id = form_data.get('product_id')
        if required[0] not in form_data:
            return json.dumps({'status': 400, 'message': 'Product Id is required'})
        cursor = conn.cursor()
        query = "SELECT product_id FROM product WHERE is_deleted = 0 and product_id = %s" % (
            product_id)
        try:
            cursor.execute(query)
            if not cursor.fetchall():
                return json.dumps({'status': 400, 'message': 'Invalid product id'})
            for key in form_data:
                if key not in update_fields + required:
                    return json.dumps({'status': 400, 'message': 'Invalid key ' + key + '/Can not update ' + key})
            form_dict = dict(form_data)
            form_dict.pop('product_id')
            form_keys = form_dict.keys()
            form_values = form_dict.values()
            form_values.append(int(product_id))
            columns = ''
            for key in form_keys:
                if key != form_keys[-1]:
                    columns += key + '= %s, '
                else:
                    columns += key + '= %s '
            query = 'UPDATE product set ' + columns + 'WHERE product_id = %s'
            cursor.execute(query, form_values)
            conn.commit()
            conn.close()
            return json.dumps({'status': 200, 'message': 'Product details Updated Successfully'})
        except:
            conn.rollback()
            conn.close()
            return json.dumps({'status': 400, 'message': 'Some error occurred'})

    def DELETE(self):
        if not is_authenticated(self):
            return json.dumps({'status': 401, 'message': 'Invalid Authentication'})
        conn = connect_mysql()
        if not conn:
            return json.dumps({'status': 400, 'message': 'Some error occurred'})
        required = ['product_id', 'is_deleted']
        form_data = web.input()
        is_deleted = form_data.get('is_deleted')
        product_id = form_data.get('product_id')
        for key in required:
            if key not in form_data:
                return json.dumps({'status': 400, 'message': key + ' is required'})
        cursor = conn.cursor()
        query = "SELECT is_deleted FROM product WHERE product_id = %s" % (
            product_id)
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            if not result:
                return json.dumps({'status': 400, 'message': 'Invalid product id'})
            if int(is_deleted) not in [0, 1]:
                return json.dumps({'status': 400, 'message': 'is_deleted must be 0/1'})
            is_deleted = int(is_deleted)
            if bool(is_deleted) == result[0][0] and is_deleted == 0:
                return json.dumps({'status': 400, 'message': 'Product is already active'})
            elif bool(is_deleted) == result[0][0] and is_deleted == 1:
                return json.dumps({'status': 400, 'message': 'Product is already deleted'})
            elif bool(is_deleted) != result[0][0] and is_deleted == 0:
                message = 'Product Activated Again Successfully'
            else:
                message = 'Product Deleted(soft) Successfully'
            query = 'UPDATE product SET is_deleted = %s WHERE product_id = %s'
            cursor.execute(query, (bool(is_deleted), product_id))
            conn.commit()
            conn.close()
            return json.dumps({'status': 200, 'message': message})
        except:
            conn.rollback()
            conn.close()
            return json.dumps({'status': 400, 'message': 'Some error occurred'})


def is_authenticated(self):
    try:
        auth = web.ctx.env.get('HTTP_AUTHORIZATION')
        if auth is None:
            pass
        else:
            auth = re.sub('^Basic ', '', auth)
            username, password = base64.b64decode(auth).decode('ascii').split(':')
            if (username, password) in allowed:
                return True
            else:
                pass
        web.header('WWW-Authenticate', 'Basic realm="Auth example"')
        web.ctx.status = '401 Unauthorized'
        return False
    except:
        return False


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run()

