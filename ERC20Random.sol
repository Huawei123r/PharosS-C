// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ERC20Random {
    string public name;
    string public symbol;
    uint8 public decimals = 18; // Common for many tokens
    uint public totalSupply;

    mapping(address => uint) public balanceOf;
    mapping(address => mapping(address => uint)) public allowance;

    event Transfer(address indexed from, address indexed to, uint value);
    event Approval(address indexed owner, address indexed spender, uint value);

    constructor(string memory _name, string memory _symbol, uint _initialSupply) {
        name = _name;
        symbol = _symbol;
        totalSupply = _initialSupply * (10**uint(decimals)); // Adjust for decimals
        balanceOf[msg.sender] = totalSupply; // Mints to deployer
    }

    function transfer(address to, uint value) public returns (bool) {
        require(balanceOf[msg.sender] >= value, "ERC20: Insufficient balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint value) public returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint value) public returns (bool) {
        require(balanceOf[from] >= value, "ERC20: Insufficient balance from");
        require(allowance[from][msg.sender] >= value, "ERC20: Insufficient allowance");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        emit Transfer(from, to, value);
        return true;
    }
}