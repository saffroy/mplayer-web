function reload() { document.location = "/" }

function action(act_name) {
    console.log("toggle " + act_name);

    const request = new XMLHttpRequest();
    request.open('GET', `/${act_name}`);
    request.onload = () => {
	if (act_name === 'stop')
	    reload();
        const response = request.responseText;
        document.querySelector('#state').innerHTML = response;
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
