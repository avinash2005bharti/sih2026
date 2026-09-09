const userModel = require('../models/user.model');
const jwt = require('jsonwebtoken')

async function authUser(req,res,next){
    const{ token } = req.cookies;
    if(!token){
        return res.status(401).json({message: "unauthorized "})    
    };
    try{
        const decode = jwt.verify(token,process.env.JWT_SECRET);

        const user = await userModel.findById(decode.id);
        req.user = user;
        next();
    }catch(err){
        res.status(401).json({message: " Unauthorized",err})
    }

}

// admin middle ware

function adminMiddleware(req, res, next) {

  if (!req.user) {
    return res.status(401).json({
      message: 'Authentication required'
    });
  }

  if (!req.user.isAdmin) {
    return res.status(403).json({
      message: 'Only admin can register new users'
    });
  }

  next();
}



module.exports = {
    authUser,
    adminMiddleware
}