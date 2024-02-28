

var page_info


function query_page_info() {
    let xmlHttp = new XMLHttpRequest()
    xmlHttp.open('GET', window.location.origin + '/get_page_info', false)
    xmlHttp.send(null)
    page_info = JSON.parse(xmlHttp.response)
}


class User_Info_Layout_Class {
    constructor (user_info_layout_id) {
        this.layout = document.getElementById(user_info_layout_id)

        this.header_elem = document.createElement('h2')
        this.name_elem = document.createElement('p')
        this.credit_elem = document.createElement('p')

        this.layout.appendChild(this.header_elem)
        this.layout.appendChild(this.name_elem)
        this.layout.appendChild(this.credit_elem)
    }

    set_header (header) {
        this.header_elem.innerHTML = header
    }

    set_name (name) {
        this.name_elem.innerHTML = `Customer Name: ${name}`
    }

    set_credit (credit) {
        this.credit_elem.innerHTML = `Customer Credit: ${credit}`
    }
}


class Selector_Class {
    constructor (parent, label) {
        this.panel = document.createElement('div')
        this.label = document.createElement('span')
        this.selector = document.createElement('select')

        this.label.innerHTML = label

        this.panel.appendChild(this.label)
        this.panel.appendChild(this.selector)
        parent.appendChild(this.panel)

        this.options = []
    }

    add_option (label, value) {
        let option
        if (this.selector.options.length == 0) {
            option = document.createElement('option')
            option.value = null
            option.label = '---- Please select ----'
            this.selector.appendChild(option)
        }
        option = document.createElement('option')
        option.value = value
        option.label = label
        this.selector.appendChild(option)
    }

    clear_option () {
        this.selector.replaceChildren()
    }
}


class Store_Items_Layout_Class {
    constructor (store_items_layout_id) {
        this.layout = document.getElementById(store_items_layout_id)
        this.header_elem = document.createElement('h2')
        this.layout.appendChild(this.header_elem)

        this.head_selector = new Selector_Class(this.layout, 'HEAD part: ')
        this.body_selector = new Selector_Class(this.layout, 'BODY part: ')
        this.arms_selector = new Selector_Class(this.layout, 'ARMS part: ')
        this.legs_selector = new Selector_Class(this.layout, 'LEGS part: ')

        this.selectors = [
            this.head_selector.selector,
            this.body_selector.selector,
            this.arms_selector.selector,
            this.legs_selector.selector
        ]

        let cart_panel = document.createElement('div')
        this.layout.appendChild(cart_panel)

        this.show_price = document.createElement('span')
        cart_panel.appendChild(this.show_price)

        this.add_to_cart_button = document.createElement('button')
        this.add_to_cart_button.textContent = 'Add to Cart'
        this.add_to_cart_button.disabled = true
        cart_panel.appendChild(this.add_to_cart_button)
    }

    set_header (header) {
        this.header_elem.innerHTML = header
    }

    clear_items () {
        this.head_selector.clear_option()
        this.body_selector.clear_option()
        this.arms_selector.clear_option()
        this.legs_selector.clear_option()
        this.add_to_cart_button.disabled = true
        this.show_price.innerHTML = ''
    }

    add_items (items_list) {
        this.items_list = items_list
        for (let item of this.items_list) {
            let selector
            switch(item[1].toLowerCase()) {
                case 'head':
                    selector = this.head_selector
                    break;
                case 'body':
                    selector = this.body_selector
                    break;
                case 'arms':
                    selector = this.arms_selector
                    break;
                case 'legs':
                    selector = this.legs_selector
                    break;
            }
            selector.add_option(`${item[2]} (${item[3]} Baht)`, item)
        }
    }

    calculate_price () {
        let have_null = false
        let price_sum = 0
        for (let selector of this.selectors) {
            let values = selector.value
            if (values != 'null') {
                price_sum += Number(selector.value.split(',')[3])
            } else {
                have_null = true
            }
        }
        if (have_null) {
            this.add_to_cart_button.disabled = true
        } else {
            this.add_to_cart_button.disabled = false
        }
        this.show_price.innerHTML = `Unit price: ${price_sum} Baht`
    }
}


class Shopping_Cart_Class {
    constructor (shopping_cart_layout_id) {
        this.layout = document.getElementById(shopping_cart_layout_id)
        this.header_elem = document.createElement('h2')
        this.layout.appendChild(this.header_elem)
        this.table = document.createElement('table')
        this.layout.appendChild(this.table)
        this.review_button = document.createElement('button')
        this.review_button.textContent = 'Review purchase'
        this.review_button.disabled = true
        this.layout.appendChild(this.review_button)

        this.cart_items = []
    }

    set_header (header) {
        this.header_elem.innerHTML = header
    }

    clear_items () {
        this.cart_items = []
        this.table.replaceChildren()
        this.review_button.disabled = true
    }

    add_unit (head_values, body_values, arms_values, legs_values) {
        let inputs = [head_values, body_values, arms_values, legs_values]
        if (this.table.childElementCount == 0) {
            let header_row = document.createElement('tr')
            this.table.appendChild(header_row)
            let col
            for (let val of ['Head', 'Body', 'Arms', 'Legs', 'Price']) {
                col = document.createElement('th')
                col.textContent = val
                header_row.appendChild(col)
            }
        }
        let data_row = document.createElement('tr')
        this.table.appendChild(data_row)
        let vals
        let col
        let sum_price = 0
        let unit_items = []
        for (let values of inputs) {
            vals = values.split(',')
            unit_items.push(Number(vals[0]))
            col = document.createElement('td')
            col.textContent = vals[2]
            sum_price += Number(vals[3])
            data_row.appendChild(col)
        }
        col = document.createElement('td')
        col.textContent = sum_price
        data_row.appendChild(col)

        this.cart_items.push(unit_items)
        this.review_button.disabled = false
    }
}


var user_info_layout = new User_Info_Layout_Class('user_info_layout')
user_info_layout.set_header('Customer infomations')

var store_items_layout = new Store_Items_Layout_Class('store_items_layout')
store_items_layout.set_header('All items in our store')

var shopping_cart = new Shopping_Cart_Class('shopping_cart')
shopping_cart.set_header('Shopping Cart')

function calculate_sum_price() {
    store_items_layout.calculate_price()
}


function add_items_to_cart() {
    let selected_values = []
    for (let selector of store_items_layout.selectors) {
        selected_values.push(selector.value)
    }
    shopping_cart.add_unit(...selected_values)
}


function goto_review_purchase() {
    let form = document.createElement('form')
    form.method = 'post'
    form.action = window.location.origin + '/review_purchase'

    let hiddenField = document.createElement('input')
    hiddenField.type = 'hidden'
    hiddenField.name = 'orders'
    hiddenField.value = JSON.stringify(shopping_cart.cart_items)
    form.appendChild(hiddenField)

    document.body.appendChild(form)
    form.submit()
}


// selector event
for (let selector of store_items_layout.selectors) {
    selector.addEventListener(
        "change", calculate_sum_price
    )
}

// add-to-cart button event
store_items_layout.add_to_cart_button.addEventListener(
    "click", add_items_to_cart
)


// review-purchase button event
shopping_cart.review_button.addEventListener(
    "click", goto_review_purchase
)


function refresh_page() {
    query_page_info()

    user_info_layout.set_name(page_info['name'])
    user_info_layout.set_credit(page_info['credit'])

    store_items_layout.clear_items()
    store_items_layout.add_items(page_info['allitems'])

    shopping_cart.clear_items()
}


refresh_page()
