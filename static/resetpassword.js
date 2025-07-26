import { sendPasswordResetEmail, getAuth } from "https://www.gstatic.com/firebasejs/9.8.1/firebase-auth.js"

window.addEventListener("load", function(){
    const forgotPasswordButton = document.getElementById('Reset-Password-Button');
    forgotPasswordButton.addEventListener('click', (clk) => handleResetPassword(clk));
});


function handleResetPassword(clk) {
    clk.preventDefault();
    const email = document.getElementById('floatingEmailForgot').value;
    const auth = getAuth();
    sendPasswordResetEmail(auth, email).then(function () {alert('Password reset email sent.')});
    window.location.replace("/login");
}

