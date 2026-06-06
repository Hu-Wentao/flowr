import 'package:fr_acdd/fr_acdd.dart';

abstract class StatelessWidget {
  const StatelessWidget({this.key});

  final Object? key;
}

/// Figma: none
/// API: account details endpoint already exists
/// Route: AppRouter.accountDetails
@FrAcddPage(mode: FrAcddMode.api, namespace: 'account_details_page')
class AccountDetailsPage extends StatelessWidget {
  const AccountDetailsPage({super.key});
}
