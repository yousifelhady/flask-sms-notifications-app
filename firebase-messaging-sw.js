importScripts('https://www.gstatic.com/firebasejs/8.2.7/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.2.7/firebase-messaging.js');

var firebaseConfig = {
    apiKey: "AIzaSyCLW3PINrtLapsUcP4B83Z6GweFI6GO0t0",
    authDomain: "swvl-notifications.firebaseapp.com",
    projectId: "swvl-notifications",
    storageBucket: "swvl-notifications.appspot.com",
    messagingSenderId: "997709666474",
    appId: "1:997709666474:web:e654121bd5ade4dd1698d3",
    measurementId: "G-3GZBG80YL9"
};

firebase.initializeApp(firebaseConfig);
const messaging=firebase.messaging();

messaging.setBackgroundMessageHandler(function (payload) {
    console.log(payload);
    const notification=JSON.parse(payload);
    const notificationOption={
        body:notification.body,
        icon:notification.icon
    };
    return self.registration.showNotification(payload.notification.title,notificationOption);
});