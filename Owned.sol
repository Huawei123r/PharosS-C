// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Owned {
    address public owner;

    // Event emitted when ownership changes
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    constructor() {
        owner = msg.sender; // The deployer becomes the owner
    }

    // Modifier to restrict functions to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _; // Continues execution of the function
    }

    // Function to transfer ownership to a new address
    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "New owner cannot be the zero address");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }

    // A dummy function only callable by the owner
    function restrictedAction() public onlyOwner returns (string memory) {
        return "Action performed by owner!";
    }
}