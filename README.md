# Usage

```python
from_addr = 'xxxx@163.com'
mail = EmailUtil(host='smtp.163.com', passwd='xxxx', port=465, from_addr=from_addr,
                 proxy_url='http://localhost:3128')
mail.send_email(from_addr, 'test', 'msg')
```