// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract RWASecurityToken is ERC20, Ownable {

    mapping(address => bool) public allowlist;
    mapping(address => bool) public blockedlist;

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
        allowlist[msg.sender] = true;
        _mint(msg.sender, initialSupply * (10 ** decimals()));
    }

    function addToAllowlist(address account) external onlyOwner {
        allowlist[account] = true;
        emit Whitelisted(account);
    }

    function removeFromAllowlist(address account) external onlyOwner {
        allowlist[account] = false;
        emit RemovedFromWhitelist(account);
    }

    function addToBlockedlist(address account) external onlyOwner {
        blockedlist[account] = true;
        emit Blacklisted(account);
    }

    function removeFromBlockedlist(address account) external onlyOwner {
        blockedlist[account] = false;
        emit RemovedFromBlacklist(account);
    }

    function mint(address to, uint256 amount) external onlyOwner {
        require(allowlist[to], "Token: receiver not allowlisted");
        require(!blockedlist[to], "Token: receiver is blocked");
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
            require(!blockedlist[from], "Token: sender is blocked");
            require(!blockedlist[to], "Token: receiver is blocked");
            require(allowlist[to], "Token: receiver not allowlisted");
        }

        super._update(from, to, value);
    }

}