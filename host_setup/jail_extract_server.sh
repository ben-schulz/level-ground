#!/bin/bash

yum update --assumeyes

packages='git wget python36 python3-pip'
yum install $packages --assumeyes
