import { signInWithEmailAndPassword, getAuth, signOut } from "https://www.gstatic.com/firebasejs/9.8.1/firebase-auth.js"

window.addEventListener("load", function(){
    const signinForm = document.getElementById('sign-in-form');
    signinForm.addEventListener('submit', (evt) => handleSignIn(evt));
});


function handleSignIn (evt) {
    evt.preventDefault();

    const signinForm = document.getElementById('sign-in-form');
    const email = signinForm['floatingEmail'].value;
    const password = signinForm['floatingPassword'].value;
    const auth = getAuth();

    signInWithEmailAndPassword(auth, email, password).then(cred => {
        if (cred.user.emailVerified) {
            signinForm.reset();
            console.log(cred);
            // Must wait until Firebase client registers the user in local storage (!!!)
            window.location.replace("/profile"); // should redirect to profile page and logged-in (Firebase logs you in automatically upon sign-up)
        }
        else {
            signOut(auth).then((e) => {
                alert("Email is not verified. Please verify your email before login.");
            });
        }
    }).catch(error => {
        if (error.code == "auth/user-not-found" || error.code == "auth/wrong-password") {alert("User and/or password are incorrect.");}
        signinForm.reset();
    });
}
