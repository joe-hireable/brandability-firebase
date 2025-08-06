// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getStorage, connectStorageEmulator } from "firebase/storage";
import { getFunctions, connectFunctionsEmulator } from "firebase/functions";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDcaKvfgqxOyf_icFAoaifk9B4hdn7tzU4",
  authDomain: "trademark-prediction-system.firebaseapp.com",
  projectId: "trademark-prediction-system",
  storageBucket: "trademark-prediction-system.appspot.com",
  messagingSenderId: "259729173809",
  appId: "1:259729173809:web:f70257ab3c56cf25fc9410",
  measurementId: "G-D257V0PL7F"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const storage = getStorage(app);

// Connect to emulators in development
if (location.hostname === "localhost") {
  connectStorageEmulator(storage, "localhost", 9199);
  const functions = getFunctions(app);
  connectFunctionsEmulator(functions, "localhost", 5004);
}