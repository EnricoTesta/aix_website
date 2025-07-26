import {getAuth, signInWithEmailAndPassword, sendEmailVerification, signOut } from "https://www.gstatic.com/firebasejs/9.8.1/firebase-auth.js"

window.addEventListener("load", function(){
    const resendVerificationButton = document.getElementById('Resend-Verification-Button');
    resendVerificationButton.addEventListener('click', (clk) => handleResendVerificationEmail(clk));
});


function handleResendVerificationEmail(clk) {
    clk.preventDefault();
    const auth = getAuth();
    const signinForm = document.getElementById('sign-in-form');
    const email = document.getElementById('floatingEmailVerify').value;
    const password = document.getElementById('floatingPasswordVerify').value;
    signInWithEmailAndPassword(auth, email, password).then(cred => {
        if (cred.user.emailVerified) {
            signinForm.reset();
            signOut(auth);
            alert('Your email is already verified.');
        }
        else {
            sendEmailVerification(auth.currentUser);
            signOut(auth);
            alert("Email verification sent.");
        }
        window.location.replace("/login");
    }).catch(error => {
        if (error.code == "auth/user-not-found" || error.code == "auth/wrong-password") {alert("User and/or password are incorrect.");}
        signinForm.reset();
    });
}
