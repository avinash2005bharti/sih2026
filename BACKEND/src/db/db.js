const mongoose = require('mongoose');

async function connectDB(){
    try{
        await mongoose.connect(process.env.MONGO_URI);
        console.log("connected to db")
    }
    catch(err){
        console.log("Error to connect with db ",err);
    }

}

module.exports = connectDB;