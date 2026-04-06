from flask import Flask, render_template, request
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text

app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost:3306/boatdb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


# render a file
@app.route('/')
def index():
    return render_template('index.html')


# remember how to take user inputs?
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


# get all boats
# this is done to handle requests for two routes -
@app.route('/boats/')
@app.route('/boats/<page>')
def get_boats(page=1):
    page = int(page)  # request params always come as strings. So type conversion is necessary.
    per_page = 10  # records to show per page
    # boats = conn.execute(text(f"SELECT * FROM boats LIMIT {per_page} OFFSET {(page - 1) * per_page}")).all()
    # print(boats)
    # return render_template('boats.html', boats=boats, page=page, per_page=per_page)
#exercise 6 - sort by id, name, price
    sort = request.args.get('sort', '')  # get the sort query param. If not present, default to empty string
    order_map = {
        'id': 'ORDER BY id',
        'name': 'ORDER BY name',
        'price_asc': 'ORDER BY rental_price ASC',
        'price_desc': 'ORDER BY rental_price DESC'
    }
    order = order_map.get(sort, '')  # get the corresponding SQL order clause. If sort is not in the map, default to empty string


#exercise 7 - filter by type and price range
    type_filter = request.args.get('type_filter', '')  # get the type query param
    min_price = request.args.get('min_price', '')  # get the minimum price query param
    max_price = request.args.get('max_price', '')  # get the maximum price query param

    conditions = []
    if type_filter:
        conditions.append(f"type = '{type_filter}'")  # add type filter condition

    if min_price:
        conditions.append(f"rental_price >= {min_price}")

    if max_price:
        conditions.append(f"rental_price <= {max_price}")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""  # construct the WHERE clause

    boats = conn.execute(text(f"SELECT * FROM boats {where} {order} LIMIT {per_page} OFFSET {(page - 1) * per_page}")).all()
    boat_types = conn.execute(text("SELECT DISTINCT type FROM boats")).all()  # get distinct boat types for filter dropdown
    return render_template('boats.html', boats=boats, page=page, per_page=per_page, sort=sort, type_filter=type_filter, min_price=min_price, max_price=max_price, boat_types=boat_types)

#exercise 2 - individual boat page
@app.route('/boats/detail/<int:boat_id>')
def boat_detail(boat_id):
    boat = conn.execute(text(f"SELECT * FROM boats WHERE id = {boat_id}")).first()
    return render_template('boat_detail.html', boat=boat)

# exercise 1 - search
@app.route('/search', methods=['GET'])
def search():
    return render_template('search.html', query=None, results=[])

@app.route('/search', methods=['POST'])
def search_post():
    query = request.form['query']
    results = conn.execute(text(f"SELECT * FROM boats WHERE name LIKE '%{query}%' OR type LIKE '%{query}%'")).all()
    return render_template('search.html', query=query, results=results)

@app.route('/create', methods=['GET'])
def create_get_request():
    return render_template('boats_create.html')


@app.route('/create', methods=['POST'])
def create_boat():
    # you can access the values with request.from.name
    # this name is the value of the name attribute in HTML form's input element
    # ex: print(request.form['id'])
    try:
        conn.execute(
            text("INSERT INTO boats values (:id, :name, :type, :owner_id, :rental_price)"),
            request.form
        )
        return render_template('boats_create.html', error=None, success="Data inserted successfully!")
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('boats_create.html', error=error, success=None)

# exercise 3 - delete boat
@app.route('/delete', methods=['GET'])
def delete_get_request():
    return render_template('boats_delete.html', boat = None, not_found=False)


@app.route('/delete', methods=['POST'])
def delete_boat():
    step = request.form.get('step')
    boat_id = request.form.get('id')

    if step == 'search':
        boat = conn.execute(text(f"SELECT * FROM boats WHERE id = {boat_id}")).first()
        if boat:
            return render_template('boats_delete.html', boat=boat, not_found=False)
        else:
            return render_template('boats_delete.html', boat=None, not_found=True)
        
    elif step == 'confirm':
        conn.execute(
            text(f"DELETE FROM boats WHERE id = :id"),
            {'id': boat_id}
        )
        conn.commit()  # commit the transaction to make the deletion permanent
        return render_template('boats_delete.html', boat=None, not_found=False, success="Boat deleted successfully!")
    
    return render_template('boats_delete.html', boat=None, not_found=False)

# exercise 4 - update boat
@app.route('/update', methods=['GET'])
def update_get():
    return render_template('boats_update.html', boat=None, not_found=False) 

@app.route('/update', methods=['POST'])
def update_boat():
    step = request.form.get('step')
    boat_id = request.form.get('id')

    if step == 'search':
        boat = conn.execute(text(f"SELECT * FROM boats WHERE id = {boat_id}")).first()
        if boat:
            return render_template('boats_update.html', boat=boat, not_found=False)
        else:
            return render_template('boats_update.html', boat=None, not_found=True)
        
    elif step == 'confirm':
            conn.execute(
                text("UPDATE boats SET name = :name, type = :type, owner_id = :owner_id, rental_price = :rental_price WHERE id = :id"),
            {
                'id': boat_id,
                'name': request.form['name'],
                'type': request.form['type'],
                'owner_id': request.form['owner_id'],
                'rental_price': request.form['rental_price'],
            })
            conn.commit()  # commit the transaction to make the update permanent
            return render_template('boats_update.html', boat=None, not_found=False, success="Boat updated successfully!")
    
    return render_template('boats_update.html', boat=None, not_found=False)


    # try:
    #     conn.execute(
    #         text("DELETE FROM boats WHERE id = :id"),
    #         request.form
    #     )
    #     return render_template('boats_delete.html', error=None, success="Data deleted successfully!")
    # except Exception as e:
    #     error = e.orig.args[1]
    #     print(error)
    #     return render_template('boats_delete.html', error=error, success=None)


if __name__ == '__main__':
    app.run(debug=True)
