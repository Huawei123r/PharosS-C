// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EtherVault {
    address public owner;

    event EthReceived(address indexed sender, uint amount);
    event EthWithdrawn(address indexed recipient, uint amount);

    constructor() {
        owner = msg.sender; // The deployer is the owner
    }

    // Fallback function to receive Ether if sent without calling a specific function
    receive() external payable {
        emit EthReceived(msg.sender, msg.value);
    }

    // Function to get the current balance of the contract
    function getBalance() public view returns (uint) {
        return address(this).balance;
    }

    // Function for the owner to withdraw all Ether
    function withdrawAll() public {
        require(msg.sender == owner, "Only owner can withdraw");
        uint balance = address(this).balance;
        require(balance > 0, "No Ether to withdraw");

        (bool success, ) = payable(owner).call{value: balance}("");
        require(success, "Failed to send Ether to owner");

        emit EthWithdrawn(owner, balance);
    }
}