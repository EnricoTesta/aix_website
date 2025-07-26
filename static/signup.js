import { createUserWithEmailAndPassword, getAuth, signOut, sendEmailVerification, updateProfile, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.8.1/firebase-auth.js"

window.addEventListener("load", function(){
    const signupForm = document.getElementById('sign-up-form');
    signupForm.addEventListener('submit', (evt) => handleSignUp(evt));
});


async function handleSignUp (evt) {
    evt.preventDefault();

    const signupForm = document.getElementById('sign-up-form');
    const email = signupForm['floatingEmail'].value;
    const password = signupForm['floatingPassword'].value;
    const username = signupForm['floatingUsername'].value;
    signupForm.reset();

    let email_domain = email.substring(email.indexOf("@"));
    if (email_domain == '@gmail.com') {
        const auth = getAuth();
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        onAuthStateChanged(auth, (user) => {if(user){updateProfile(user, {displayName: username})}else{}});
        verify_and_setup(userCredential.user, email, username);
        signOut(auth).then((e) => {window.location.replace("/login")});
    }
    else {
        alert("Failed to create user. You need a gmail domain to sign-up.")
    }
}

function verify_and_setup (user, email, username) {
   console.log(user);
   sendEmailVerification(user);
   alert("We sent a verification email to your address. Please verify your email to sign in.");
   backend_user_setup(user.uid, email, username);
}

function backend_user_setup (user_uid, email, username) {
    fetch('/backend_user_setup',
        {method:'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user:user_uid, user_email:email, user_name:username})})
        .then((r) => {console.log(r)})
}