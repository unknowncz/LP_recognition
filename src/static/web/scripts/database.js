
controls = document.getElementById('controls');
results = document.getElementById('results');
localStorage.removeItem('lastQueryResults');
localStorage.setItem('lastSelectedTable', 'query');

function construct_html(json) {
    html = '';
    json.forEach(element => {
        html += '<tr>';
        Object.values(element).forEach(value => {
            html += (element===json[0]?'<th>':'<td>') + value + (element===json[0]?'</th>':'</td>');
        });
        html += '</tr>';
    });
    if (html == '') {
        html = '<tr><td>No results found</td></tr>';
    }
    return html;
}

function submit_query(query, table) {
    xhr = new XMLHttpRequest();
    xhr.open('GET', '/database?query='+query, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            console.log('Query submitted and processed');
            if (table == 'query') {
                results.innerHTML = construct_html(JSON.parse(xhr.responseText));
            } else {
                refresh_table(table);
            }
        }
    }
    xhr.send();
}

function refresh_table(table) {
    xhr = new XMLHttpRequest();
    xhr.open('GET', '/database?table='+table, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            console.log('Table refreshed');
            results.innerHTML = construct_html(JSON.parse(xhr.responseText));
        }
    }
    xhr.send();
}

controls.children[2].addEventListener('submit', function(event) {
    console.log('Form submitted');
    event.preventDefault();
    query = document.getElementById('query').value;
    table = document.getElementById('tableSelector').value;
    submit_query(query, table);
});

controls.children[2].addEventListener('click', function(event) {
    console.log('Form submitted');
    event.preventDefault();
    query = document.getElementById('query').value;
    table = document.getElementById('tableSelector').value;
    submit_query(query, table);
});

controls.children[0].addEventListener('change', function() {
    table = document.getElementById('tableSelector').value;
    if (localStorage.getItem('lastSelectedTable') == 'query' && table != 'query') {
        localStorage.setItem('lastQueryResults', results.innerHTML)
    }
    localStorage.setItem('lastSelectedTable', table);
    if (table == 'query') {
        document.getElementById('query').disabled = false;
        console.log(localStorage.getItem('lastQueryResults'));
        results.innerHTML = localStorage.getItem('lastQueryResults');
    } else {
        document.getElementById('query').disabled = true;
        refresh_table(table);
    }
});

document.body.children[document.body.children.length-2].addEventListener('click', function() {
    window.location.href = '/'
});
