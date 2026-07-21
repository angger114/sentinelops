package compliance

deny[msg] {
  some i
  input[i].public == true
  msg := sprintf("resource %s is publicly exposed", [input[i].resourceId])
}

deny[msg] {
  some i
  input[i].encrypted == false
  msg := sprintf("resource %s is not encrypted", [input[i].resourceId])
}
