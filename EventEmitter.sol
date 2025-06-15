// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EventEmitter {
    // Define an event with indexed parameters for easy filtering
    event MessageEmitted(address indexed sender, string message, uint timestamp);

    // Constructor (optional, can be empty or take an initial message)
    constructor() {
        // No specific constructor arguments needed for this example,
        // but it could take an initial message.
    }

    // Function to emit the event
    function emitMyMessage(string memory _message) public {
        emit MessageEmitted(msg.sender, _message, block.timestamp);
    }
}