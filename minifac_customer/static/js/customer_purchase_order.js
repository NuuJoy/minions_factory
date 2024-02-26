

var page_info


function query_page_info() {
    let xmlHttp = new XMLHttpRequest()
    xmlHttp.open('GET', window.location.origin + '/get_page_info', false)
    xmlHttp.send(null)
    page_info = JSON.parse(xmlHttp.response)
}


function refresh_customer_info() {
    let customer_info = ''
    customer_info += 'Customer Name: ' + page_info['name'] + '<br>'
    customer_info += 'Customer Credit: ' + page_info['credit']
    document.getElementById('customer_info').innerHTML = customer_info
}


function get_selector(part_name) {
    return document.getElementById(part_name.toLowerCase() + '_select')
}


function clear_selector(part_name) {
    let select = get_selector(part_name)
    select.replaceChildren()
    let opt = document.createElement('option')
    opt.value = null
    opt.innerHTML = '---- Please select ----'
    select.appendChild(opt)
}


function clear_all_selectors() {
    for (let part_name of ['head', 'body', 'arms', 'legs']) {
        clear_selector(part_name)
    }
}


function refresh_page() {
    query_page_info()
    refresh_customer_info()
    clear_all_selectors()
    let opt
    for (let item of page_info['allitems']) {
        let id = item[0]
        let part_name = item[1]
        let color = item[2]
        let price = item[3]
        opt = document.createElement('option')
        opt.value = id
        opt.innerHTML = color + ' (' + price + ' Bath)'
        get_selector(part_name).appendChild(opt)
    }
    clear_price_calculation()
}


function get_value_by_id(id, index) {
    for (let item of page_info['allitems']) {
        if (item[0] == id) {
            return item[index]
        }
    }
}


function get_selected_item_id(part_name) {
    return get_selector(part_name).value
}


function get_selected_item_color(part_name) {
    return get_value_by_id(get_selected_item_id(part_name), 2)
}


function get_selected_item_price(part_name) {
    return get_value_by_id(get_selected_item_id(part_name), 3)
}


function clear_price_calculation() {
    let price_cal = document.getElementById('price_calculation')
    price_cal.replaceChildren()
}


function calculate_price() {
    clear_price_calculation()

    let total_price = 0.0
    let id
    let color
    let price
    let tr
    let td
    let tbl = document.createElement('table')
    for (let part_name of ['Head', 'Body', 'Arms', 'Legs']) {
        id = get_selected_item_id(part_name)
        if (id != 'null') {
            tr = tbl.insertRow()

            td = tr.insertCell()
            td.innerHTML = part_name

            color = get_selected_item_color(part_name)
            td = tr.insertCell()
            td.innerHTML = color

            price = get_selected_item_price(part_name)
            total_price += Number(price)
            td = tr.insertCell()
            td.innerHTML = price
        }
    }

    let price_cal = document.getElementById('price_calculation')
    price_cal.appendChild(tbl)

    let total_price_text = document.createElement('p')
    total_price_text.innerHTML = 'Total price: ' + total_price
    price_cal.appendChild(total_price_text)
}

refresh_page()
