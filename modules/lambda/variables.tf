variable "fn_name" {
  type = string
}

variable "code_path" {
  type = string
}

variable "handler" {
  type = string
}

variable "runtime" {
  type    = string
  default = "python3.7"
}

variable "timeout" {
  type    = number
  default = 60
}

variable "iam_policy_definition" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
