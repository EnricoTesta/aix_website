window.addEventListener("load", function(){
    document.getElementById('challenge-select-leaderboard').value = 'aix__stock_market';
    getRoundNumber();
    refresh_leaderboard();
    const challengeSelect = document.getElementById('challenge-select-leaderboard');
    challengeSelect.onchange = (evt) => toggleChallenge(evt);
});


const createScoreboardTable = () => {
    const scoreDiv = document.getElementById("scoreboard") // Find the scoreboard div in our html
    let tableHeaders = ["Ranking", "Username", "Weight", "Prize"]

    //while (scoreDiv.firstChild) scoreDiv.removeChild(scoreDiv.firstChild) // Remove all children from scoreboard div (if any)
    let scoreboardTable = document.createElement('table') // Create the table itself
    scoreboardTable.className = 'scoreboardTable'
    let scoreboardTableHead = document.createElement('thead') // Creates the table header group element
    scoreboardTableHead.className = 'scoreboardTableHead'
    let scoreboardTableHeaderRow = document.createElement('tr') // Creates the row that will contain the headers
    scoreboardTableHeaderRow.className = 'scoreboardTableHeaderRow'

    // Will iterate over all the strings in the tableHeader array and will append the header cells to the table header row
    tableHeaders.forEach(header => {
        let scoreHeader = document.createElement('th') // Creates the current header cell during a specific iteration
        scoreHeader.innerText = header
        scoreboardTableHeaderRow.append(scoreHeader) // Appends the current header cell to the header row
    })

    scoreboardTableHead.append(scoreboardTableHeaderRow) // Appends the header row to the table header group element
    scoreboardTable.append(scoreboardTableHead)

    let scoreboardTableBody = document.createElement('tbody') // Creates the table body group element
    scoreboardTableBody.className = "scoreboardTable-Body"
    scoreboardTable.append(scoreboardTableBody) // Appends the table body group element to the table
    scoreDiv.append(scoreboardTable) // Appends the table to the scoreboard div
}

// The function below will accept a single score and its index to create the global ranking
const appendScores = (singleScore, singleScoreIndex) => {
    const scoreboardTable = document.querySelector('.scoreboardTable') // Find the table we created
    let scoreboardTableBodyRow = document.createElement('tr') // Create the current table row
    scoreboardTableBodyRow.className = 'scoreboardTableBodyRow'

    // Create the 5 column cells that will be appended to the current table row
    let ranking = document.createElement('td')
    ranking.innerText = singleScoreIndex
    let user = document.createElement('td')
    user.innerText = singleScore.user_id
    let weight = document.createElement('td')
    weight.innerText = singleScore.weight
    let prize = document.createElement('td')
    prize.innerText = singleScore.prize

    scoreboardTableBodyRow.append(ranking, user, weight, prize) // Append all 5 cells to the table row
    scoreboardTable.append(scoreboardTableBodyRow) // Append the current row to the scoreboard table body
}

function refresh_leaderboard() {
    try {
        let formData = new FormData();
        formData.append("challenge", document.getElementById('challenge-select-leaderboard').value);
    fetch('/backend_get_leaderboard', {method: 'POST', body: formData})
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            createScoreboardTable();
            appendLeaderboard(data);
        })
        .catch(function (err) {
            console.log('error: ' + err);
        }); }
    catch (err) {
        console.log('error: ' + err);
    }
}

function appendLeaderboard(data) {
    const scoreboardTable = document.querySelector('.scoreboardTable')

    for (var i = 0; i < data.user.length; i++) {
        let scoreboardTableBodyRow = document.createElement('tr') // Create the current table row
        scoreboardTableBodyRow.className = 'scoreboardTableBodyRow'

        let ranking = document.createElement('td')
        ranking.innerText = (i+1).toString()
        let user = document.createElement('td')
        user.innerText = data.user[i]
        let weight = document.createElement('td')
        weight.innerText = data.weight[i]
        let prize = document.createElement('td')
        prize.innerText = '$' + data.prize[i]

        scoreboardTableBodyRow.append(ranking, user, weight, prize) // Append all 5 cells to the table row
        scoreboardTable.append(scoreboardTableBodyRow)
    }
}

function getRoundNumber() {
    let formData = new FormData();
    formData.append("challenge", document.getElementById('challenge-select-leaderboard').value);
    fetch('/backend_get_prize_round_number', {method: 'POST', body: formData})
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                document.getElementById("Round_Number").innerHTML = data['round_number'];
            })
            .catch(function (err) {
                console.log('error: ' + err);
            });
}

function toggleChallenge(evt) {
    evt.preventDefault();
    document.getElementById("scoreboard").innerHTML = ''
    refresh_leaderboard();
    getRoundNumber();
}