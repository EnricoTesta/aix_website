import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/9.8.1/firebase-auth.js"

window.addEventListener("load", function(){
    onAuthStateChanged(getAuth(), user => toggleElementVisibility(user));

    const logoutButton = document.getElementById('Logout');
    logoutButton.addEventListener('click', (clk) => handleLogout(clk));
});

function toggleElementVisibility(user) {
    if (user) {
        // User is signed in, so display the "sign out" button and login info.
        let elementsToHide = ['Login', 'sign-up']
        let elementsToShow = ['Logout', 'profile-page']
        for (let i = 0; i < elementsToHide.length; i++) {
            hideElement(elementsToHide[i]);
        }
        for (let i = 0; i < elementsToShow.length; i++) {
            showElement(elementsToShow[i]);
        }

        console.log(`Signed in as ${user.displayName} (${user.email})`);

        user.getIdToken().then(function (token) {
            // Add the token to the browser's cookies. The server will then be
            // able to verify the token against the API.
            // SECURITY NOTE: As cookies can easily be modified, only put the
            // token (which is verified server-side) in a cookie; do not add other
            // user information.
            document.cookie = "token=" + token;
        });
    } else {
        // User is signed out.
        // Initialize the FirebaseUI Widget using Firebase.
        //var ui = new firebaseui.auth.AuthUI(firebase.auth());
        // Show the Firebase login button.
        // ui.start('#firebaseui-auth-container', uiConfig);
        // Update the login state indicators.
        let elementsToHide = ['Logout', 'profile-page']
        let elementsToShow = ['Login', 'sign-up']
        for (let i = 0; i < elementsToHide.length; i++) {
            hideElement(elementsToHide[i]);
        }
        for (let i = 0; i < elementsToShow.length; i++) {
            showElement(elementsToShow[i]);
        }

        // Clear the token cookie.
        document.cookie = "token=";
    }
}

function hideElement(e) {
    const element = document.getElementById(e);
    if (element) {element.hidden = true}
}

function showElement(e) {
    const element = document.getElementById(e);
    if (element) {element.hidden = false}
}

function handleLogout(clk) {
    clk.preventDefault();
    signOut(getAuth()).then((e) => {window.location.replace("/")});
}
