function reload() { document.location = "/" }

function refresh_state() {
    const request = new XMLHttpRequest();
    request.open('GET', '/state');
    request.onload = () => {
        const response = request.responseText;
        document.querySelector('#state').innerHTML = response;
    };
    request.send();
}

function action(act_name) {
    console.log("toggle " + act_name);

    const request = new XMLHttpRequest();
    request.open('GET', `/${act_name}`);
    request.onload = () => {
	if (act_name === 'stop')
	    reload();
	refresh_state();
    };
    request.send();
}

function chosen_file() {
    const idx = document.querySelector('#file-select').value;
    console.log("chose " + idx);

    const request = new XMLHttpRequest();
    request.open('GET', `/select?idx=${idx}`);
    request.onload = reload;
    request.send();
}

function register_load() {
    document.addEventListener('readystatechange', event => {
	if (event.target.readyState === 'complete') {
	    refresh_state();
	}
    });
}
