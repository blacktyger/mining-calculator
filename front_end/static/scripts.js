// Running Loop keeping alive connection with back-end

document.addEventListener('DOMContentLoaded', function () {
    keep_alive_server()
    try {setInterval(keep_alive_server, 5 * 1000)()
    } catch (error) {}
});

function keep_alive_server() {
    fetch(document.location + "keep-alive/?alive=true", {
        method: 'GET',
        cache: 'no-cache'
    })
        .then(resp => resp.json())
        .then(data => {
            document.getElementById("heightText").innerHTML = data.height
            document.getElementById("algoIcon").innerHTML = data.algo.icon
            document.getElementById("algoText").innerHTML = data.algo.text
            document.getElementById("deltaText").innerHTML = data.delta

        })
        .catch(error => {console.error(error)});
    }


function apiCall(body, query, cbFieldId, method='POST') {
    fetch(query, {
        method: method,
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body),
    })
        .then(resp => resp.text())  // or, resp.json(), etc.
        .then(data => {
            document.getElementById(cbFieldId).innerHTML = data
        })
        .catch(error => {
            console.error(error)
        });
}