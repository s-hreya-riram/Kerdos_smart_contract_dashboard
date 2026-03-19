/*  Defining the Token module for hardhat ignition, this module will be used to deploy and interact with 
    the Token contract in our tests.
    This is similar to the module in https://github.com/s-hreya-riram/SmartContract/blob/main/ignition/modules/Token.js
*/
const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

module.exports = buildModule("TokenModule", (m) => {
    const token = m.contract("RWASecurityToken", [
        "Kerdos",   
        "KRDS",                
        1000000n,             
    ]);
    return { token };
});