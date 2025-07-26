import { getAuth, onAuthStateChanged, deleteUser, signOut, reauthenticateWithCredential } from "https://www.gstatic.com/firebasejs/9.8.1/firebase-auth.js"

window.addEventListener("load", function(){

    document.getElementById('challenge-select').value = "aix__stock_market";

    const auth = getAuth();
    const challengeSelect = document.getElementById('challenge-select');
    onAuthStateChanged(auth, user => refresh_user_display_name(user));
    onAuthStateChanged(auth, user => refresh_credits_and_wallet(user));
    onAuthStateChanged(auth, user => refresh_metrics(user, challengeSelect.value));
    onAuthStateChanged(auth, user => refresh_code_quality(user, challengeSelect.value));
    onAuthStateChanged(auth, user => refresh_logs(user, challengeSelect.value));
    onAuthStateChanged(auth, user => refresh_active_submission(user, challengeSelect.value));
    onAuthStateChanged(auth, user => refresh_job_running_status(user, challengeSelect.value));

    const deleteAccountButton = document.getElementById('deleteAccountButton');
    const uploadButton = document.getElementById('upload-button');
    const datalabButton = document.getElementById('datalab-button');
    const activateSubmissionButton = document.getElementById('activate-submission-button');
    deleteAccountButton.addEventListener('click', (clk) => handleDelete(clk));
    uploadButton.addEventListener('click', (evt) => handleFileUpload(evt));
    datalabButton.addEventListener('click', (evt) => go_to_datalab(evt));
    activateSubmissionButton.addEventListener('click', (evt) => activateSubmission(evt));
    challengeSelect.onchange = (evt) => toggleChallenge(evt);

});

async function activateSubmission(evt) {
    evt.preventDefault()
    let formData = new FormData();
    const auth = getAuth();
    formData.append("user", auth.currentUser.uid);
    formData.append("challenge", document.getElementById('challenge-select').value)
    let s = await fetch('/backend_activate_submission', {method: 'POST', body: formData});
    if (s.status == 200) {
        location.reload();
    } else if (s.status == 401) {
        alert("Insufficient credits. Please buy credits and try again.")
    } else if (s.status == 402) {
        alert("No code uploaded. Please upload your code and try again.")
    } else if (s.status == 403) {
        alert("Quality certificate not found. If a job is pending, try again after it's done. Otherwise, please review" +
            " code requirements.")
    }
}

function toggleChallenge(evt) {
    evt.preventDefault();
    const auth = getAuth();
    const challenge = document.getElementById('challenge-select').value;
    refresh_metrics(auth.currentUser, challenge);
    refresh_code_quality(auth.currentUser, challenge);
    refresh_logs(auth.currentUser, challenge);
    refresh_active_submission(auth.currentUser, challenge);
    refresh_job_running_status(auth.currentUser, challenge);
}

function refresh_metrics(user, challenge) {
    try {
        let formData = new FormData();
        formData.append("user", user.uid);
        formData.append("challenge", challenge)
        fetch('/backend_get_metrics', {method: 'POST', body: formData})
            .then(function (response) {
                //return response;
                return response.json();
            })
            .then(function (data) {
                Object.keys(data).forEach(function(key) {displayMetric(key, data[key])})
            })
            .catch(function (err) {
                console.log('error: ' + err);
            });
    } catch (err) {
        console.log(err);
    }
}

function displayMetric(key, value) {

    document.getElementById("metrics").innerHTML = '';

    let key_div = document.createElement("div");
    key_div.className = "col-sm-6"
    key_div.innerHTML = key;

    let value_div = document.createElement("div");
    value_div.className = "col-sm-6"
    value_div.innerHTML = value;

    document.getElementById("metrics").appendChild(key_div);
    document.getElementById("metrics").appendChild(value_div);
}

function displayCodeQuality(value) {

    document.getElementById("code-quality").innerHTML = '';

    let value_div = document.createElement("div");
    value_div.className = "col-sm-6"
    value_div.innerHTML = value;

    document.getElementById("code-quality").appendChild(value_div);
}

function go_to_datalab(evt) {
    evt.preventDefault()
    let formData = new FormData();
    const auth = getAuth();
    formData.append("user", auth.currentUser.uid);
    fetch('/backend_get_user_dataset', {method: 'POST', body: formData})
        .then(function (response) {
            return response.text();
        })
        .then(function (dataset) {
            let prefix = "https://console.cloud.google.com/bigquery?authuser=0&cloudshell=false&project=aix-backend-prod&p=aix-backend-prod&d="
            let suffix = "&page=dataset"
            let full_url = prefix.concat(dataset).concat(suffix)
            window.open(full_url, '_blank').focus();
        })
        .catch(function (err) {
            console.log('error: ' + err);
        });

}

function refresh_user_display_name(user) {
    try {
        let formData = new FormData();
        formData.append("user", user.uid);
        fetch('/backend_get_user_displayname', {method: 'POST', body: formData})
            .then(function (response) {
                //return response;
                return response.json();
            })
            .then(function (data) {
                document.getElementById("displayName").innerHTML = '\n' + data['display_name'];
            })
            .catch(function (err) {
                console.log('error: ' + err);
            });
    } catch (err) {
        console.log(err);
    }
}

function refresh_active_submission(user, challenge) {
    try {
        let formData = new FormData();
        formData.append("user", user.uid);
        formData.append("challenge", challenge)
        fetch('/backend_get_submission_status', {method: 'POST', body: formData})
            .then(function (response) {
                //return response;
                return response.text();
            })
            .then(function (data) {
                document.getElementById("ActiveInCurrentRound").innerHTML = '\n' + data;
            })
            .catch(function (err) {
                console.log('error: ' + err);
            });
    } catch (err) {
        console.log(err);
    }
}

function refresh_logs(user, challenge) {
    try {
        let formData = new FormData();
        formData.append("user", user.uid);
        formData.append("challenge", challenge);
        fetch('/backend_get_logs', {method: 'POST', body: formData})
            .then(function (response) {
                //return response;
                return response.text();
            })
            .then(function (data) {
                document.getElementById("LogData").innerHTML = '\n' + data;
            })
            .catch(function (err) {
                console.log('error: ' + err);
            });
    } catch (err) {
        console.log(err);
    }
}

function refresh_code_quality(user, challenge) {
    try {
        let formData = new FormData();
        formData.append("user", user.uid);
        formData.append("challenge", challenge);
        fetch('/backend_get_code_quality', {method: 'POST', body: formData})
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                document.getElementById("codeQuality").innerHTML = data['Quality']
                document.getElementById("processQuality").innerHTML = ''
                document.getElementById("transformQuality").innerHTML = ''
                if (data['Quality'] == 'KO') {
                    var process_string = '\n'
                    for (var key of Object.keys(data['process'])) {
                        process_string += key + ', '
                    }
                    let process_string_length = process_string.length
                    var transform_string = '\n'
                    for (var key of Object.keys(data['transform'])) {
                        transform_string += key + ', '
                    }
                    let transform_string_length = transform_string.length
                    document.getElementById("processQuality").innerHTML = 'Process quality issues:\n' + process_string.substring(1, process_string_length-2)
                    document.getElementById("transformQuality").innerHTML = 'Transform quality issues:\n' + transform_string.substring(1, transform_string_length-2)
                }
            })
            .catch(function (err) {
                console.log('error: ' + err);
            });
    } catch (err) {
        console.log(err);
    }
}

function refresh_credits_and_wallet(user) {
    try {
        let formData = new FormData();
        formData.append("user", user.uid);
        fetch('/backend_get_user_credits_and_wallet', {method: 'POST', body: formData})
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                document.getElementById("UserCredits").innerHTML = data['credits'];
                document.getElementById("UserWallet").innerHTML = data['wallet'].concat('$');
            })
            .catch(function (err) {
                console.log('error: ' + err);
            });
    } catch (err) {
        console.log(err);
    }
}

function refresh_job_running_status(user, challenge) {
    try {
        let formData = new FormData();
        formData.append("user", user.uid);
        formData.append("challenge", challenge);
        fetch('/backend_get_job_running_status', {method: 'POST', body: formData})
            .then(function (response) {
                //return response;
                return response.text();
            })
            .then(function (data) {
                document.getElementById("JobRunning").innerHTML = data;
            })
            .catch(function (err) {
                console.log('error: ' + err);
            });
    } catch (err) {
        console.log(err);
    }
}

async function handleDelete(clk) {
    clk.preventDefault();

    alert("Your account is about to be deleted. Please wait a few seconds...");

    let formData = new FormData();
    const auth = getAuth();
    formData.append("user", auth.currentUser.uid);
    formData.append("email", auth.currentUser.email);

    let r = await fetch('/backend_delete_user',{method: "POST", body: formData});
    console.log('HTTP response code:', r.status);
    if(r.status == 200) {
        const auth2 = getAuth();
        const user = auth2.currentUser;
        deleteUser(user);
        signOut(auth).then((e) => {window.location.replace("/")});
        alert("Your account is deleted.");
    } else {
        alert("Something went wrong. Please try again.")
    }
}

async function handleFileUpload(evt) {

    let formData = new FormData();
    let fileToUpload = document.getElementById("fileUpload").files[0];

    const auth = getAuth();
    formData.append("file", fileToUpload);
    formData.append("user", auth.currentUser.uid);
    formData.append("challenge", document.getElementById("challenge-select").value);

    // const ctrl = new AbortController()    // timeout
    // setTimeout(() => ctrl.abort(), 5000);
    document.getElementById("fileUpload") // .reset()
    try {
        // let r = await fetch('/backend_upload_file',
        //     {method: "POST", body: formData, signal: ctrl.signal});
        alert("Upload may take several seconds. Please wait...");
        let r = await fetch('/backend_upload_file',
            {method: "POST", body: formData});
        console.log('HTTP response code:',r.status);
        if (r.status == 200) {
            alert("Upload successful! Your code will start running shortly...");
            location.reload();
        } else {
            const m = await r.text()
            alert(m)
        }
    } catch(e) {
        alert("Something went wrong. Please try again.")
        console.log('Huston we have problem...:', e);
    }
}