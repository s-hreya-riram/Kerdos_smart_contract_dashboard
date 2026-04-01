// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract RWASecurityToken is ERC20, Ownable {

    mapping(address => bool) public whitelist;
    mapping(address => bool) public blacklist;

    event Whitelisted(address indexed account);
    event RemovedFromWhitelist(address indexed account);
    event Blacklisted(address indexed account);
    event RemovedFromBlacklist(address indexed account);
    event TransferBlocked(address indexed from, address indexed to, uint256 amount, string reason);

    constructor(
        string memory name_,
        string memory symbol_,
        uint256 initialSupply
    ) ERC20(name_, symbol_) Ownable(msg.sender) {
        whitelist[msg.sender] = true;
        _mint(msg.sender, initialSupply * (10 ** decimals()));
    }

    function addToWhitelist(address account) external onlyOwner {
        whitelist[account] = true;
        emit Whitelisted(account);
    }

    function removeFromWhitelist(address account) external onlyOwner {
        whitelist[account] = false;
        emit RemovedFromWhitelist(account);
    }

    function addToBlacklist(address account) external onlyOwner {
        blacklist[account] = true;
        emit Blacklisted(account);
    }

    function removeFromBlacklist(address account) external onlyOwner {
        blacklist[account] = false;
        emit RemovedFromBlacklist(account);
    }

    function mint(address to, uint256 amount) external onlyOwner {
        require(whitelist[to], "Token: receiver not whitelisted");
        require(!blacklist[to], "Token: receiver is blacklisted");
        _mint(to, amount * (10 ** decimals()));
    }

    function burn(address from, uint256 amount) external onlyOwner {
        _burn(from, amount * (10 ** decimals()));
    }

    function _update(
        address from,
        address to,
        uint256 value
    ) internal override {
        bool isMint = (from == address(0));
        bool isBurn = (to == address(0));

        if (!isMint && !isBurn) {
            require(!blacklist[from], "Token: sender is blacklisted");
            require(!blacklist[to], "Token: receiver is blacklisted");
            require(whitelist[to], "Token: receiver not whitelisted");
        }

        super._update(from, to, value);
    }

}